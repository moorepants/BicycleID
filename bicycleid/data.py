import os
import pandas
import numpy as np
from scipy.io import loadmat
import bicycledataprocessor.main as bdp
from bicycledataprocessor.database import get_row_num

from config import (PATH_TO_SYSTEM_ID_DATA, PATH_TO_DATABASE, PATH_TO_H5,
        PATH_TO_CORRUPT)

class ExperimentalData(object):

    states = ['Phi', 'Delta', 'PhiDot', 'DeltaDot']
    inputs = ['TDelta']

    def __init__(self):
        self.build_data_frame()

    def build_data_frame(self):
        self.fileName = PATH_TO_SYSTEM_ID_DATA
        mat = loadmat(self.fileName, squeeze_me=True)

        d = {}
        d['RunID'] = [os.path.splitext(str(r))[0] for r in mat['matFiles']]
        d['Speed'] = mat['speeds']

        for fit in mat['fits']:
            for i, state in enumerate(self.states):
                try:
                    d[state + 'Fit'].append(fit[i])
                except KeyError:
                    d[state + 'Fit'] = [fit[i]]

        d['MeanFit'] = np.mean(mat['fits'], 1)

        for A in mat['stateMatrices']:
            for i in range(2, 4):
                for j in range(len(self.states)):
                    col = 'a' + str(i + 1) + str(j + 1)
                    try:
                        d[col].append(A[i, j])
                    except KeyError:
                        d[col] = [A[i, j]]

        for B in mat['inputMatrices']:
            for i in range(2, 4):
                col = 'b' + str(i + 1) + str(1)
                try:
                    d[col].append(B[i])
                except KeyError:
                    d[col] = [B[i]]

        dataset = bdp.DataSet(fileName=PATH_TO_DATABASE, pathToH5=PATH_TO_H5,
                pathToCorruption=PATH_TO_CORRUPT)
        dataset.open()

        table = dataset.database.root.runTable

        tableCols = ['Rider', 'Maneuver', 'Environment', 'Duration']

        for col in tableCols:
            d[col] = []

        for r in d['RunID']:
            i = get_row_num(r, table)
            for col in tableCols:
                d[col].append(table[i][col])

        dataset.close()

        self.dataFrame = pandas.DataFrame(d)

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

        """

        df = self.dataFrame

        for col in ['Rider', 'Maneuver', 'Environment']:
            if col in kwargs.keys():
                # todo: this is sorta hacky, something better is needed
                # this is for a spelling error in the data set
                if col == 'Environment' and 'Pavilion' in kwargs[col]:
                    kwargs[col].append('Pavillion Floor')
                if col == 'Environment' and 'Treadmill' in kwargs[col]:
                    kwargs[col].append('Horse Treadmill')
                df = df[df[col].isin(kwargs[col])]

        for col in ['MeanFit', 'Duration']:
            if col in kwargs.keys():
                df = df[df[col] > kwargs[col]]

        # todo: add the ability to slice with respect to the individual fits

        return df
