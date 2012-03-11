import numpy as np
from matplotlib import rc
import matplotlib.figure as mpfig
import matplotlib.backends.backend_gtk as mpgtk
from dtk import control
import bicycleparameters as bp

class CoefficientPlot(object):

    equations = [r'\dot{\phi}', r'\dot{\delta}', r'\ddot{\phi}', r'\ddot{\delta}']
    states = [r'\phi', r'\delta', r'\dot{\phi}', r'\dot{\delta}']
    xlabel = r'$v$ $\frac{m}{s}$'
    xlim = (1.0, 10.0)
    ylim = np.array([[-10., 30.],
                     [-60., 0.],
                     [-4., 2.],
                     [-3., 3.],
                     [-0.5, 0.5],
                     [-50., 300.],
                     [-175., 40.],
                     [-50., 50.],
                     [-40., 20.],
                     [-5., 15.]])
    riderNames = ['Charlie', 'Jason', 'Luke']

    def __init__(self):

        rc('figure.subplot', wspace=0.4, hspace=0.4)
        self.figure = mpfig.Figure(figsize=(6, 4), dpi=60)
        self.axes = {}

        self.title = self.figure.suptitle('')

        for i in range(2, 4):
            for j in range(4):
                label = 'a' + str(i + 1) + str(j + 1)
                ax = self.figure.add_subplot(2, 5, 5 * (i - 2) + j + 1)
                self.axes[label] = ax
                ax.set_title('$a_{' + self.equations[i] + self.states[j] + '}$')
                ax.set_xlabel(self.xlabel)
                ax.set_xlim(self.xlim)
                ax.set_ylim(self.ylim[5 * (i - 2) + j])

        for i, p in zip(range(2, 4), [5, 10]):
            label = 'b' + str(i + 1) + str(1)
            ax = self.figure.add_subplot(2, 5, p)
            self.axes[label] = ax
            ax.set_title('$b_{' + self.equations[i] + r'T_\delta' + '}$')
            ax.set_xlabel(self.xlabel)
            ax.set_xlim(self.xlim)
            ax.set_ylim(self.ylim[p - 1])

        self.lines = {}
        for label, ax in self.axes.items():
            self.lines[label + '-exp'] = ax.plot(self.xlim, [1., 1.], '.',
                    markersize=2)[0]
            for rider in self.riderNames:
                self.lines[label + '-mod-' + rider] = ax.plot(self.xlim, [1., 1.])[0]

        self.canvas = mpgtk.FigureCanvasGTK(self.figure)
        self.canvas.show()

    def update_graph(self, exp, mod):
        """Sets the data in the plot with respect to the provided experimental
        and model data sets.

        Parameters
        ----------
        exp : pandas.DataFrame
            A data frame containing the experimental data.
        mod : dictionary
            A dictionary of pandas.DataFrame objects containing the data for
            each rider.

        """

        self.title.set_text('Number of experiments: {}'.format(len(exp)))
        for name, line in self.lines.items():
            try:
                label, typ, rider = name.split('-')
            except ValueError:
                label, typ = name.split('-')

            if typ == 'exp':
                line.set_data(exp['ActualSpeed'], exp[label])
            elif typ == 'mod':
                try:
                    line.set_data(mod[rider]['Speed'], mod[rider][label])
                except KeyError:
                    line.set_data([np.nan], [np.nan])

class BodePlot(object):

    inputNames = [r'$T_\delta$']
    outputNames = [r'$\phi$', r'$\delta$']
    stateNames = [r'$\phi$', r'$\delta$', r'$\dot{\phi}$', r'$\dot{\delta}$']
    systemNames = ['Experimental Mean', 'Experimental Upper Uncertainty',
            'Experimental Lower Uncertainty', 'Charlie', 'Jason', 'Luke']
    colors = ['b', 'b', 'b', 'r', 'g', 'm']
    linestyles = ['-', '--', '--', '-', '-', '-']

    def __init__(self, w):

        A = np.array([[  0.        ,   0.        ,   1.        ,   0.        ],
                      [  0.        ,   0.        ,   0.        ,   1.        ],
                      [  8.24494689,  -3.53782098,  -0.06418077,  -0.53855055],
                      [ 18.84406429,  31.38819183,   3.50835159,  -7.18282895]])

        B = np.array([[ 0.        ],
                      [ 0.        ],
                      [-0.1018712 ],
                      [ 5.56864583]])

        C = np.array([[1., 0., 0., 0.],
                      [0., 1., 0., 0.]])

        D = np.zeros((2, 1))

        self.systems = []
        for name in self.systemNames:
            self.systems.append(control.StateSpace(A, B, C, D, name=name,
                inputNames=self.inputNames, outputNames=self.outputNames,
                stateNames=self.stateNames))

        self.w = w

        self.bode = control.Bode(w, *self.systems, colors=self.colors,
                linestyles=self.linestyles)
        self.bode.mag_phase()
        self.bode.plot()

        self.canvases = []
        for fig in self.bode.figs:
            canvas = mpgtk.FigureCanvasGTK(fig)
            self.canvases.append(canvas)
            canvas.show()

    def update_graph(self, bodeData, models):
        """Updates the Bode plot based on the provided data.

        Parameters
        ----------
        bodeData : tuple
            The mean and standard deviation of the magnitude and phase and the
            mean speed for the set of runs.
        models : dictionary
            A dictionary of models for each rider.

        """
        meanMag, stdMag, meanPhase, stdPhase, meanSpeed, stdSpeed = bodeData

        meanMagPlus = meanMag + stdMag
        meanMagMinus = meanMag - stdMag

        # steer torque to roll angle
        phiPlot = self.bode.figs[0]
        phiPlot.magAx.lines[0].set_ydata(meanMag[:, 0, 0])
        phiPlot.magAx.lines[1].set_ydata(meanMagPlus[:, 0, 0])
        phiPlot.magAx.lines[2].set_ydata(meanMagMinus[:, 0, 0])
        phiPlot.magAx.set_ylim((-100, 50))

        phiPlot.phaseAx.lines[0].set_ydata(meanPhase[:, 0, 0])
        phiPlot.phaseAx.lines[1].set_ydata(meanPhase[:, 0, 0] + stdPhase[:, 0, 0])
        phiPlot.phaseAx.lines[2].set_ydata(meanPhase[:, 0, 0] - stdPhase[:, 0, 0])
        phiPlot.phaseAx.set_ylim((-360, 0))

        # steer torque to steer angle
        deltaPlot = self.bode.figs[1]
        deltaPlot.magAx.lines[0].set_ydata(meanMag[:, 1, 0])
        deltaPlot.magAx.lines[1].set_ydata(meanMagPlus[:, 1, 0])
        deltaPlot.magAx.lines[2].set_ydata(meanMagMinus[:, 1, 0])
        deltaPlot.magAx.set_ylim((-100, 50))

        deltaPlot.phaseAx.lines[0].set_ydata(meanPhase[:, 1, 0])
        deltaPlot.phaseAx.lines[1].set_ydata(meanPhase[:, 1, 0] + stdPhase[:, 1, 0])
        deltaPlot.phaseAx.lines[2].set_ydata(meanPhase[:, 1, 0] - stdPhase[:, 1, 0])
        deltaPlot.phaseAx.set_ylim((-360, 0))

        for rider in ['Charlie', 'Jason', 'Luke']:
            try:
                mod = models[rider]
            except KeyError:
                # if the rider isn't there, don't plot the lines
                lenW = len(deltaPlot.magAx.lines[0].get_xdata())
                mag = np.nan * np.ones((lenW, 2))
                phase = np.nan * np.ones((lenW, 2))
            else:
                mag, phase = mod.magnitude_phase(meanSpeed, self.w)
                mag = 20. * np.log10(mag)
                phase = np.rad2deg(phase)

                for i, p in enumerate(phase.T):
                    if p[0] > 0.:
                        phase[:, i] = phase[:, i] - 360.

            phiPlot.magAx.lines[self.systemNames.index(rider)].set_ydata(mag[:, 0])
            phiPlot.phaseAx.lines[self.systemNames.index(rider)].set_ydata(phase[:, 0])
            deltaPlot.magAx.lines[self.systemNames.index(rider)].set_ydata(mag[:, 1])
            deltaPlot.phaseAx.lines[self.systemNames.index(rider)].set_ydata(phase[:, 1])

class RootLociPlot(object):
    def __init__(self, models, expSpeed, eig, speed):
        # the plot should have eigenvalues for each rider in a different color
        # and plot dots for the eigenvalues from the model

        self.fig = bp.plot_eigenvalues([mod.bicycle for mod in models.values()], speed)

        # plot eigenvalues of the experimental models
        self.ax = self.fig.axes[0]
        self.ax.set_ylim((-10., 10.))


        #self.real = self.ax.plot(expSpeed, np.real(eig), '.k')
        self.real = []
        for eigs in eig.T:
            eigWithImag = abs(np.imag(eigs)) > 1e-10
            self.real.append(self.ax.scatter(expSpeed, np.real(eigs),
                c=eigWithImag))
        self.imag = self.ax.plot(expSpeed, abs(np.imag(eig)), 'ob')

        self.canvas = mpgtk.FigureCanvasGTK(self.fig)
        self.canvas.show()

    def update_plot(self, speed, eig):
        for i, line in enumerate(self.real):
            xy = np.vstack((speed, np.real(eig[:, i]))).T
            line.set_offsets(xy)
        for i, line in enumerate(self.imag):
            line.set_data(speed, abs(np.imag(eig[:, i])))
