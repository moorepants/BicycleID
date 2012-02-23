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

class Gui:

    target = ""

    riders = ['charlie', 'jason', 'luke']
    environments = ['treadmill', 'pavilion']
    maneuvers = ['balance', 'balanceDisturb', 'track', 'trackDisturb']

    toggleButtonNames = {}
    toggleButtonNames['Rider'] = [x + 'Button' for x in riders]
    toggleButtonNames['Environment'] = [x + 'Button' for x in environments]
    toggleButtonNames['Maneuver'] = [x + 'Button' for x in maneuvers]

    def __init__(self):

        fileName = "BicycleID.glade"
        self.builder = gtk.Builder()
        self.builder.add_from_file(fileName)

        self.mainWindow = self.builder.get_object('mainWindow')

        # set the default toggle button states
        self.get_toggle_button_states()

        # make the initial plot
        self.coefPlot = plot.CoefficientPlot()
        self.plotBox = self.builder.get_object("plotBox")
        self.plotBox.pack_start(self.coefPlot.canvas, True, True)

        # load the initial experimental data
        self.data = data.ExperimentalData()
        # load all the rider models
        self.models = {}
        for r in self.riders:
            rider = r.capitalize()
            self.models[rider] = model.Whipple(rider)

        self.state_to_dict()
        self.load_exp_data()
        self.load_mod_data()
        self.select_rider_model()

        self.initialize_parameters()

        # update graph with initial data
        self.update_graph()

        dic = {
            'on_mainWindow_destroy' : gtk.main_quit,
            'on_charlieButton_toggled': self.change_toggle_state,
            'on_jasonButton_toggled': self.change_toggle_state,
            'on_lukeButton_toggled': self.change_toggle_state,
            'on_treadmillButton_toggled': self.change_toggle_state,
            'on_pavilionButton_toggled': self.change_toggle_state,
            'on_balanceButton_toggled': self.change_toggle_state,
            'on_trackButton_toggled': self.change_toggle_state,
            'on_balanceDisturbButton_toggled': self.change_toggle_state,
            'on_trackDisturbButton_toggled': self.change_toggle_state,
            'on_meanFitSpinButton_value_changed': self.update_mean_fit
            }

        for par in self.models['Jason'].parameters.keys():
            dic['on_' + par + '_SpinButton_value_changed'] = \
                self.change_parameter

        self.builder.connect_signals(dic)

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

    def change_parameter(self, widget):
        name = gtk.Buildable.get_name(widget).split('_')[0]
        add = widget.get_value()
        for rider, model in self.models.items():
            model.set_parameter(name, model.defaultParameters[name] + add)
        self.load_mod_data()
        self.select_rider_model()
        self.update_graph()

    def get_toggle_button_states(self):
        """Gets the current toggle button states and stores them in a
        dictionary."""

        self.toggleStates = {k:{} for k in self.toggleButtonNames.keys()}
        for k, v in self.toggleButtonNames.items():
            for name in v:
                button = self.builder.get_object(name)
                self.toggleStates[k][name] = button.get_active()

    def load_exp_data(self):
        """Loads the subset of the experimental data."""
        self.exp = self.data.subset(**self.subsetDict)

    def load_mod_data(self):
        """Computes the model output data for each rider and stores it in
        self.mod."""
        speeds = np.linspace(self.coefPlot.xlim[0],
                             self.coefPlot.xlim[1],
                             num=5)
        self.mod = {}
        for rider in self.riders:
            self.mod[rider.capitalize()] = \
                    self.models[rider.capitalize()].matrices(speeds)

    def select_rider_model(self):
        """Set the selected models based on the riders in self.subset."""
        self.modSelect = {}
        for rider in self.subsetDict['Rider']:
            self.modSelect[rider] = self.mod[rider]

    def update_mean_fit(self, widget):
        """Callback for adjusting the mean fit spin button."""
        self.state_to_dict()
        self.load_exp_data()
        self.update_graph()

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

    def update_graph(self):
        """Redraws the plot based on the current experimental and model
        data."""
        self.coefPlot.update_graph(self.exp, self.modSelect)
        self.coefPlot.canvas.draw()

    def change_toggle_state(self, widget):
        """The callback for the factor toggle buttons."""
        name = gtk.Buildable.get_name(widget)
        for k, v in self.toggleStates.items():
            if name in v.keys():
                self.toggleStates[k][name] = widget.get_active()

        self.state_to_dict()
        self.load_exp_data()
        self.select_rider_model()
        self.update_graph()

gui = Gui()
gui.mainWindow.show()
gtk.main()
