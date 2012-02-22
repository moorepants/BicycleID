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

        self.builder.connect_signals(dic)

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

        # update graph with initial data
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
        self.exp = self.data.subset(**self.subsetDict)

    def load_mod_data(self):
        """Computes the model output data for each rider and stores it in
        self.mod."""
        speeds = np.linspace(self.coefPlot.xlim[0],
                             self.coefPlot.xlim[1],
                             num=20)
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
        self.state_to_dict()
        self.load_exp_data()
        self.update_graph()

    def state_to_dict(self):
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
        self.coefPlot.update_graph(self.exp, self.modSelect)
        self.coefPlot.canvas.draw()

    def change_toggle_state(self, widget):
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
