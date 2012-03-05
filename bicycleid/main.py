#!/usr/bin/env python

import pygtk
pygtk.require("2.0")

import matplotlib
matplotlib.use('GTK')

import gtk
import gtk.glade

import numpy as np

# local dependencies
import data
import model
import plot

# debugging
try:
    from IPython.core.debugger import Tracer
except ImportError:
    pass
else:
    set_trace = Tracer()

class Gui:

    riders = ['charlie', 'jason', 'luke']
    environments = ['treadmill', 'pavilion']
    maneuvers = ['balance', 'balanceDisturb', 'track', 'trackDisturb']
    speeds = ['1.4', '2.0', '3.0', '4.0', '4.92', '5.8', '7.0', '9.0']

    toggleButtonNames = {}
    toggleButtonNames['Rider'] = [x + 'Button' for x in riders]
    toggleButtonNames['Environment'] = [x + 'Button' for x in environments]
    toggleButtonNames['Maneuver'] = [x + 'Button' for x in maneuvers]
    toggleButtonNames['Speed'] = [x + 'Button' for x in speeds]

    bodeFrequency = np.logspace(-1, 2., num=200)
    eigSpeed = np.linspace(0., 10., num=100)

    def __init__(self):

        fileName = "BicycleID.glade"
        self.builder = gtk.Builder()
        self.builder.add_from_file(fileName)

        self.mainWindow = self.builder.get_object('mainWindow')

        # set the default toggle button states
        self.get_toggle_button_states()

        # load the initial experimental data
        print('Loading the experimental data...')
        self.data = data.ExperimentalData(w=self.bodeFrequency)
        # load all the rider models
        print('Loading the first principles models...')
        self.models = {}
        for r in self.riders:
            rider = r.capitalize()
            self.models[rider] = model.Whipple(rider)

        self.update_coef_data()

        self.initialize_parameters()

        # make the initial plots
        print('Initializing plots...')
        self.initialize_coef_plot()
        self.initialize_bode_plots()
        self.initialize_root_loci_plot()

        # update the coef graph with initial data
        self.update_coef_graph()

        dic = {
            'on_mainWindow_destroy' : gtk.main_quit,
            'on_charlieButton_toggled': self.change_toggle_state,
            'on_jasonButton_toggled': self.change_toggle_state,
            'on_lukeButton_toggled': self.change_toggle_state,
            'on_treadmillButton_toggled': self.change_toggle_state,
            'on_pavilionButton_toggled': self.change_toggle_state,
            'on_balanceButton_toggled': self.change_toggle_state,
            'on_trackButton_toggled': self.change_toggle_state,
            'on_1.4Button_toggled': self.change_toggle_state,
            'on_2.0Button_toggled': self.change_toggle_state,
            'on_3.0Button_toggled': self.change_toggle_state,
            'on_4.0Button_toggled': self.change_toggle_state,
            'on_4.92Button_toggled': self.change_toggle_state,
            'on_5.8Button_toggled': self.change_toggle_state,
            'on_7.0Button_toggled': self.change_toggle_state,
            'on_9.0Button_toggled': self.change_toggle_state,
            'on_balanceDisturbButton_toggled': self.change_toggle_state,
            'on_trackDisturbButton_toggled': self.change_toggle_state,
            'on_meanFitSpinButton_value_changed': self.update_mean_fit,
            'on_plotNotebook_switch_page': self.change_plot,
            }

        for par in self.models['Jason'].parameters.keys():
            dic['on_' + par + '_SpinButton_value_changed'] = \
                self.change_parameter

        self.builder.connect_signals(dic)

    ## Callbacks ##

    def change_plot(self, notebook, page, pageNum):
        currentPage = notebook.get_nth_page(pageNum)
        name = gtk.Buildable.get_name(currentPage)
        if name == 'coefTab':
            self.update_coef_data()
            self.update_coef_graph()
        elif name == 'bodeTab':
            self.set_speed_toggle_to_group()
            self.update_bode_data()
            self.update_bode_plot()
        elif name == 'eigTab':
            self.update_eig_data()
            self.update_root_loci_plot()
        else:
            raise Exception('No plot named {}.'.format(name))

    def change_parameter(self, widget):
        name = gtk.Buildable.get_name(widget).split('_')[0]
        add = widget.get_value()
        for rider, model in self.models.items():
            model.set_parameter(name, model.defaultParameters[name] + add)
        self.load_mod_data()
        self.select_rider_model()
        self.update_coef_graph()

        # todo: make this bode plot aware

    def update_mean_fit(self, widget):
        """Callback for adjusting the mean fit spin button."""
        plotTab = self.get_current_plot_tab()
        self.state_to_dict()
        if plotTab == 'coefTab':
            self.load_exp_data()
            self.update_coef_graph()
        elif plotTab == 'bodeTab':
            self.update_bode_data()
            self.update_bode_plot()
        elif plotTab == 'eigTab':
            self.update_eig_data()
            self.update_root_loci_plot()
        else:
            raise Exception('No tab named {}.'.format(plotTab))

    def change_toggle_state(self, widget):
        """The callback for the factor toggle buttons."""
        name = gtk.Buildable.get_name(widget)

        for k, v in self.toggleStates.items():
            if name in v.keys():
                self.toggleStates[k][name] = widget.get_active()

        plotTab = self.get_current_plot_tab()

        self.state_to_dict()

        if plotTab == 'coefTab':
            self.update_coef_data()
            self.update_coef_graph()
        elif plotTab == 'bodeTab':
            self.update_bode_data()
            self.update_bode_plot()
        elif plotTab == 'eigTab':
            self.update_eig_data()
            self.update_root_loci_plot()
        else:
            raise Exception('No tab named {}.'.format(plotTab))

    ## Helper Functions ##

    def get_toggle_button_states(self):
        """Gets the current toggle button states and stores them in a
        dictionary."""

        self.toggleStates = {k:{} for k in self.toggleButtonNames.keys()}
        for k, v in self.toggleButtonNames.items():
            for name in v:
                button = self.builder.get_object(name)
                self.toggleStates[k][name] = button.get_active()

    def state_to_dict(self):
        """Converts the state of the wigdets used for subsetting the data and
        writes a dictionary which can be passed to the ExperimentalData subset
        method."""
        self.subsetDict = {}
        for butTyp, buttons in self.toggleStates.items():
            l = []
            for butName, state in buttons.items():
                if state is True:
                    label = self.builder.get_object(butName).get_label()
                    l.append(label)
            self.subsetDict[butTyp] = l

        self.subsetDict['MeanFit'] = \
                self.builder.get_object('meanFitSpinButton').get_value()

    def get_current_plot_tab(self):
        """Returns the current plot tab name."""
        plotNotebook = self.builder.get_object('plotNotebook')
        pageNum = plotNotebook.get_current_page()
        currentPage = plotNotebook.get_nth_page(pageNum)
        return gtk.Buildable.get_name(currentPage)

    def set_speed_toggle_to_group(self):
        """Toggles all of the speed buttons off except for 2.0."""
        for speedButton in self.toggleButtonNames['Speed']:
            button = self.builder.get_object(speedButton)
            if button.get_active() and not speedButton.startswith('2.0'):
                button.set_active(False)
            elif not button.get_active() and speedButton.startswith('2.0'):
                button.set_active(True)

    ## Coefficient Plots ##

    def initialize_coef_plot(self):
        self.coefPlot = plot.CoefficientPlot()
        self.plotBox = self.builder.get_object("plotBox")
        self.plotBox.pack_start(self.coefPlot.canvas, True, True)

    def load_exp_data(self):
        """Loads the subset of the experimental data."""
        self.exp = self.data.subset(**self.subsetDict)

    def load_mod_data(self):
        """Computes the model output data for each rider and stores it in
        self.mod."""
        speeds = np.linspace(0., 10., num=8)
        self.mod = {}
        for rider in self.riders:
            self.mod[rider.capitalize()] = \
                    self.models[rider.capitalize()].matrices(speeds)

    def select_rider_model(self):
        """Set the selected models based on the riders in self.subset."""
        self.modSelect = {}
        for rider in self.subsetDict['Rider']:
            self.modSelect[rider] = self.mod[rider]

    def update_coef_data(self):
        self.state_to_dict()
        self.load_exp_data()
        self.load_mod_data()
        self.select_rider_model()

    def update_coef_graph(self):
        """Redraws the plot based on the current experimental and model
        data frames."""
        self.coefPlot.update_graph(self.exp, self.modSelect)
        self.coefPlot.canvas.draw()

    ## Bode Plots ##

    def initialize_bode_plots(self):

        self.bodePlot = plot.BodePlot(self.bodeFrequency)

        self.phiBodePlotBox = self.builder.get_object("phiBodePlotBox")
        self.phiBodePlotBox.pack_start(self.bodePlot.canvases[0], True, True)

        self.deltaBodePlotBox = self.builder.get_object("deltaBodePlotBox")
        self.deltaBodePlotBox.pack_start(self.bodePlot.canvases[1], True, True)

    def update_bode_data(self):
        """Returns a subset of the magnitude and phase data for the
        experiment"""
        self.state_to_dict()
        self.bodeSubset = self.data.subset_bode(**self.subsetDict)
        # todo: this should make a subset of models to pass to
        # self.bodePlot.update_graph, so that only the riders that are selected
        # get plotted

    def update_bode_plot(self):
        self.bodePlot.update_graph(self.bodeSubset, self.models)
        self.bodePlot.canvases[0].draw()
        self.bodePlot.canvases[1].draw()

    ## Root Loci Plot ##

    def initialize_root_loci_plot(self):
        self.update_eig_data()
        self.rootLociPlot = plot.RootLociPlot(self.models, self.expEigSpeed,
                self.eigSubset, self.eigSpeed)
        self.rootLociPlotBox = self.builder.get_object("rootLociPlotBox")
        self.rootLociPlotBox.pack_start(self.rootLociPlot.canvas, True, True)

    def update_eig_data(self):
        self.state_to_dict()
        self.expEigSpeed, self.eigSubset = self.data.subset_eig(**self.subsetDict)

    def update_root_loci_plot(self):
        self.rootLociPlot.update_plot(self.expEigSpeed, self.eigSubset)
        self.rootLociPlot.canvas.draw()

    ## Model Parameters ##

    def initialize_parameters(self):
        for par, val in self.models['Jason'].parameters.items():
            lower = val - 2 * val
            upper = val + 2 * val
            step_inc = 0.05 * val
            page_inc = 0.05 * val
            adj = gtk.Adjustment(0., lower, upper, step_inc, page_inc, 0.)
            button = self.builder.get_object(par + '_SpinButton')
            if button is not None:
                button.set_adjustment(adj)

gui = Gui()
gui.mainWindow.show()
gtk.main()
