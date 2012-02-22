import numpy as np
import pandas
import bicycleparameters as bp

from config import PATH_TO_PARAMETERS

class FirstPrinciplesModel(object):

    possibleRiders = ['Charlie', 'Jason', 'Luke']

    def __init__(self):
        pass

    def set_default_parameters(self):
        for k, v in self.defaultParameters.items():
            self.parameters[k] = v

    def set_parameter(self, var, val):
        """Sets a model parameter.

        Parameters
        ----------
        var : string
            A variable name of a model parameter.
        val : float
            A parameter value.

        """

        if var not in self.parameters.keys():
            print('{} is not a valid parameter.'.format(var))
        else:
            self.parameters[var] = val

    def set_parameters(self, parDict):
        """Sets the model parameters.

        Parameters
        ----------
        parDict : dictionary
            A dictionary of parameters to change. The variable names must match
            the variables stored in self.parameters.

        """
        for var, val in parDict.items():
            self.set_parameter(var, val)

    def matrices(self, speedRange):
        """Returns the state and input matrices for a range of speeds.

        Parameters
        ----------
        speedRange : array_like, shape(n,)
            A range of speeds in meters per second increasing in value.

        Returns
        -------
        dataframe : pandas.DataFrame
            The columns are speed with the state and input matric entries for
            the acceleration equations. The states are [roll angle, steer
            angle, roll rate, steer rate]. The input are [steer torque].

        """
        A = np.zeros((len(speedRange), 4, 4))
        B = np.zeros((len(speedRange), 4))

        for i, speed in enumerate(speedRange):
            A[i], B[i] = self.state_space(speed)

        d = {}

        d['Speed'] = speedRange

        for i in range(2, 4):
            for j in range(4):
                col = 'a' + str(i + 1) + str(j + 1)
                d[col] = A[:, i, j]

        for i in range(2, 4):
            col = 'b' + str(i + 1) + str(1)
            d[col] = B[:, i]

        dataframe = pandas.DataFrame(d)

        return dataframe

class Whipple(FirstPrinciplesModel):
    """A first principles model for the Whipple model."""

    parDir = PATH_TO_PARAMETERS

    def __init__(self, rider):
        """Sets the parameters of the model for the supplied rider.

        Parameters
        ----------
        rider : string
            Either `Charlie`, `Jason`, or `Luke`.

        """

        if rider not in self.possibleRiders:
            raise ValueError('{} is not a valid rider.'.format(rider))

        self.rider = rider
        if self.rider == 'Jason':
            self.bicycleName = 'Rigid'
        else:
            self.bicycleName = 'Rigidcl'

        self.bicycle = bp.Bicycle(self.bicycleName, pathToData=self.parDir,
                forceRawCalc=True)
        self.bicycle.add_rider(self.rider)
        self.parameters = self.bicycle.parameters['Benchmark']
        self.defaultParameters = bp.io.remove_uncertainties(self.parameters)

    def state_space(self, speed):
        """Returns the state and input matrix for the Whipple bicycle model.

        Parameters
        ----------
        speed : float
            The speed at which to compute the state space model.

        Returns
        -------
        A : ndarray, shape(4,4)
            The state matrix with states [roll angle, steer angle, roll rate,
            steer rate].
        B : ndarray, shape(4,)
            The input matrix with inputs [steer torque].

        """
        A, BFull = self.bicycle.state_space(speed, nominal=True)
        B = BFull[:, 1]

        return A, B
