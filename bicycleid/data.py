import os
import pandas
import numpy as np
from scipy.io import loadmat
import bicycledataprocessor as bdp
from bicycledataprocessor.database import get_row_num
from dtk import control

# debugging
try:
    from IPython.core.debugger import Tracer
except ImportError:
    pass
else:
    set_trace = Tracer()

from config import (PATH_TO_SYSTEM_ID_DATA, PATH_TO_DATABASE, PATH_TO_H5,
        PATH_TO_CORRUPT)

class ExperimentalData(object):

    states = ['Phi', 'Delta', 'PhiDot', 'DeltaDot']
    inputs = ['TDelta']

    def __init__(self, fileName=None, w=None):
        """Loads a .mat file and data from the database to construct a
        data frame."""

        if fileName is None:
            self.fileName = PATH_TO_SYSTEM_ID_DATA
        else:
            self.fileName = fileName

        if w is None:
            w = np.logspace(-1.0, 1.0, num=100)

        mat = loadmat(self.fileName, squeeze_me=True)

        d = {}

        d['RunID'] = [os.path.splitext(str(r))[0] for r in mat['matFiles']]
        d['ActualSpeed'] = mat['speeds']
        d['Duration'] = mat['durations']

        for fit in mat['fits']:
            for i, state in enumerate(self.states):
                try:
                    d[state + 'Fit'].append(fit[i])
                except KeyError:
                    d[state + 'Fit'] = [fit[i]]

        d['MeanFit'] = np.mean(mat['fits'], 1)

        self.stateMatrices = mat['stateMatrices']

        for A in mat['stateMatrices']:
            for i in range(2, 4):
                for j in range(len(self.states)):
                    col = 'a' + str(i + 1) + str(j + 1)
                    try:
                        d[col].append(A[i, j])
                    except KeyError:
                        d[col] = [A[i, j]]

        self.inputMatrices = mat['inputMatrices']

        for B in mat['inputMatrices']:
            for i in range(2, 4):
                col = 'b' + str(i + 1) + str(1)
                try:
                    d[col].append(B[i, 0])
                except KeyError:
                    d[col] = [B[i, 0]]

        dataset = bdp.DataSet(fileName=PATH_TO_DATABASE, pathToH5=PATH_TO_H5,
                pathToCorruption=PATH_TO_CORRUPT)
        dataset.open()

        table = dataset.database.root.runTable

        tableCols = ['Rider', 'Maneuver', 'Environment', 'Speed']

        for col in tableCols:
            d[col] = []

        for r in d['RunID']:
            i = get_row_num(r, table)
            for col in tableCols:
                d[col].append(table[i][col])

        dataset.close()

        self.dataFrame = pandas.DataFrame(d)

        self.w = w

        self.load_bode_data()
        self.load_eig_data()

    def load_bode_data(self):
        """Computes the magnitude and phase information for the steer torque to
        roll angle and steer angle transfer functions for each of the
        identified runs.

        Parameters
        ----------
        w : ndarray, shape(n,)
            The frequencies in radians/second.

        """

        numRuns = self.stateMatrices.shape[0]

        C = np.array([[1., 0., 0., 0.],
                      [0., 1., 0., 0.]])
        D = np.zeros((2, 1))

        self.magnitudes = np.zeros((numRuns, len(self.w), 2, 1))
        self.phases = np.zeros((numRuns, len(self.w), 2, 1))

        for i, A in enumerate(self.stateMatrices):
            B = self.inputMatrices[i][:, 0].reshape((4, 1))
            sys = control.StateSpace(A, B, C, D)
            bode = control.Bode(self.w)
            self.magnitudes[i], self.phases[i] = bode.mag_phase_system(sys)

    def subset_bode(self, **kwargs):
        """Returns the mean and standard deviation of the magnitude and phase
        curves for the subset of data.

        Parameters
        ----------
        same as ExperimentalData.subset()


        Returns
        -------
        meanMag : ndarray, shape(n, 2, 1)
            The average of the magnitudes of the two transfer functions for n
            frequencies.
        stdMag : ndarray, shape(n, 2, 1)
            The standard deviation of the magnitudes of the two transfer
            functions for n frequencies.
        meanPhase : ndarray, shape(n, 2, 1)
            The average of the magnitudes of the two transfer functions for n
            frequencies.
        stdPhase : ndarray, shape(n, 2, 1)
            The standard deviation of the magnitudes of the two transfer
            functions for n frequencies.

        """

        df = self.subset(**kwargs)
        meanSpeed = df['ActualSpeed'].mean()
        stdSpeed = df['ActualSpeed'].std()

        indices = self.dataFrame['RunID'].isin(df['RunID'])

        subMags = self.magnitudes[indices]
        subPhases = self.phases[indices]

        # if the phase curve is in the 0 to 2 * pi region, shift it into the 0
        # to - 2 * pi region
        #for i, phaseMat in enumerate(subPhases):
            #for j in range(phaseMat.shape[0]):
                #if subPhases[i, j, 0] > 0.:
                    #subPhases[i, j, :] = subPhases[i, j, :] - 2 * np.pi

        matchFreq = 0.1
        matchPhase = -np.pi * np.ones((2, 1))

        adjustedSubPhases = np.zeros_like(subPhases)
        for i, run in enumerate(subPhases):
            firstPhase = run[0, :, :]
            correctPhase = np.mod(firstPhase, 2 * np.pi)
            changeInPhase = firstPhase - correctPhase
            for j, freq in enumerate(run):
                adjustedSubPhases[i, j] = freq - changeInPhase - 2 * np.pi

        # convert to dB and degrees, then calculate the mean and standard
        # deviations
        magDB = 20.0 * np.log10(subMags)
        phaseDeg = np.rad2deg(adjustedSubPhases)

        meanMag = magDB.mean(axis=0)
        stdMag = magDB.std(axis=0)

        meanPhase = phaseDeg.mean(axis=0)
        stdPhase = phaseDeg.std(axis=0)

        #meanPhase = subPhases.mean(axis=0)
        #stdPhase = subPhases.std(axis=0)

        return meanMag, stdMag, meanPhase, stdPhase, meanSpeed, stdSpeed

    def subset(self, **kwargs):
        """Returns a subset of the experimental data based on the provided
        lists.

        Parameters
        ----------
        Rider : list
            A list of riders: `Charlie`, `Jason` or `Luke`.
        Maneuver : list
            A list of maneuvers: `Balance`, `Balance With Disturbance`, `Track
            Straight Line`, or `Track Straight Line With Disturbance`.
        Environment : list
            A list of environments: `Treadmill` or `Pavilion`
        Speed : list
            A list of speed bins: '1.4', '2.0', '3.0', '4.0', '4.92', '5.8',
            '7.0', '9.0'
        MeanFit : float
            The minimum mean fit value for the output fits.
        Duration : float
            The minimum duration of the runs.
        """

        df = self.dataFrame

        for col in ['Rider', 'Maneuver', 'Environment']:
            if col in kwargs.keys():
                # todo: The first if is for the spelling error in the data and
                # the second is just because I wrote Treadmill everwhere else,
                # forgetting that the data is "Horse Treadmill".
                if col == 'Environment' and 'Pavilion' in kwargs[col]:
                    kwargs[col].append('Pavillion Floor')
                if col == 'Environment' and 'Treadmill' in kwargs[col]:
                    kwargs[col].append('Horse Treadmill')
                df = df[df[col].isin(kwargs[col])]

        if 'Speed' in kwargs.keys():
            allSpeeds = set(['1.4', '2.0', '3.0', '4.0', '4.92', '5.8', '7.0', '9.0'])
            for speed in allSpeeds.difference(set(kwargs['Speed'])):
                df = df[abs(df['Speed'] - float(speed)) > 1e-5]

        for col in ['MeanFit', 'Duration']:
            if col in kwargs.keys():
                df = df[df[col] > kwargs[col]]

        # todo: add the ability to slice with respect to the individual fits

        return df

    def load_eig_data(self):

        self.eig = np.zeros((self.stateMatrices.shape[0], 4),
                dtype=np.complex64)

        for i, A in enumerate(self.stateMatrices):
            self.eig[i] = np.linalg.eig(A)[0]

    def subset_eig(self, **kwargs):

        df = self.subset(**kwargs)

        indices = self.dataFrame['RunID'].isin(df['RunID'])

        return df['ActualSpeed'], self.eig[indices]
