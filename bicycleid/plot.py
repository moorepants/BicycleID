import numpy as np
from matplotlib import rc
import matplotlib.figure as mpfig
import matplotlib.backends.backend_gtk as mpgtk

class CoefficientPlot(object):

    equations = [r'\dot{\phi}', r'\dot{\delta}', r'\ddot{\phi}', r'\ddot{\delta}']
    states = [r'\phi', r'\delta', r'\dot{\phi}', r'\dot{\delta}']
    xlabel = r'$v$ $\frac{m}{s^2}$'
    xlim = (1., 8.)
    ylim = np.array([[0., 20.],
                       [-80., 0.],
                       [-1.5, 4.],
                       [-8., 0.],
                       [-0.2, 1.2],
                       [0., 200.],
                       [-175., 40.],
                       [-40., 60.],
                       [-100., 0.],
                       [0., 20.]])
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
            self.lines[label + '-exp'] = ax.plot(self.xlim, [1., 1.], '.')[0]
            for rider in self.riderNames:
                self.lines[label + '-mod-' + rider] = ax.plot(self.xlim, [1., 1.])[0]

        self.canvas = mpgtk.FigureCanvasGTK(self.figure)
        self.canvas.show()

    def update_graph(self, exp, mod):

        self.title.set_text('Number of experiments: {}'.format(len(exp)))
        for name, line in self.lines.items():
            try:
                label, typ, rider = name.split('-')
            except ValueError:
                label, typ = name.split('-')

            if typ == 'exp':
                line.set_data(exp['Speed'], exp[label])
            elif typ == 'mod':
                try:
                    line.set_data(mod[rider]['Speed'], mod[rider][label])
                except KeyError:
                    line.set_data([np.nan], [np.nan])
