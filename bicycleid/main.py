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
            "on_mainWindow_destroy" : gtk.main_quit,
            'on_charlieButton_toggled': self.change_toggle_state,
            'on_jasonButton_toggled': self.change_toggle_state,
            'on_lukeButton_toggled': self.change_toggle_state,
            'on_treadmillButton_toggled': self.change_toggle_state,
            'on_pavilionButton_toggled': self.change_toggle_state,
            'on_balanceButton_toggled': self.change_toggle_state,
            'on_trackButton_toggled': self.change_toggle_state,
            'on_balanceDisturbButton_toggled': self.change_toggle_state,
            'on_trackDisturbButton_toggled': self.change_toggle_state,
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
        self.expData = data.ExperimentalData()
        # load all the rider models
        self.model = {}
        for r in self.riders:
            rider = r.capitalize()
            self.model[rider] = model.Whipple(rider)
        self.load_exp_data()
        self.load_mod_data()
        self.select_rider_model()

        # update graph with initial data
        self.update_graph()

    def get_toggle_button_states(self):
        self.toggleStates = {k:{} for k in self.toggleButtonNames.keys()}
        for k, v in self.toggleButtonNames.items():
            for name in v:
                button = self.builder.get_object(name)
                self.toggleStates[k][name] = button.get_active()

    def load_exp_data(self):

        subsetDict = self.toggle_state_to_dict()
        self.exp = self.expData.subset(**subsetDict)

    def load_mod_data(self):
        speeds = np.linspace(self.coefPlot.xlim[0],
                             self.coefPlot.xlim[1],
                             num=20)
        self.mod = {}
        for rider in self.riders:
            self.mod[rider.capitalize()] = \
                    self.model[rider.capitalize()].matrices(speeds)

    def select_rider_model(self):
        subsetDict = self.toggle_state_to_dict()
        self.modSelect = {}
        for rider in subsetDict['Rider']:
            self.modSelect[rider] = self.mod[rider]

    def toggle_state_to_dict(self):
        subsetDict = {}
        for butTyp, buttons in self.toggleStates.items():
            l = []
            for butName, state in buttons.items():
                if state is True:
                    label = self.builder.get_object(butName).get_label()
                    l.append(label)
            subsetDict[butTyp] = l

        return subsetDict

    def update_graph(self):
        self.coefPlot.update_graph(self.exp, self.modSelect)
        self.coefPlot.canvas.draw()

    def change_toggle_state(self, widget):
        name = gtk.Buildable.get_name(widget)
        for k, v in self.toggleStates.items():
            if name in v.keys():
                self.toggleStates[k][name] = widget.get_active()
        self.load_exp_data()
        self.select_rider_model()
        self.update_graph()

gui = Gui()
gui.mainWindow.show()
gtk.main()
