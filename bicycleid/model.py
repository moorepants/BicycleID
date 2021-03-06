import numpy as np
import pandas
import bicycleparameters as bp
from dtk import control

# debugging
try:
    from IPython.core.debugger import Tracer
except ImportError:
    pass
else:
    set_trace = Tracer()

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
            angle, roll rate, steer rate]. The input are [steer torque, lateral
            force].

        """
        A = np.zeros((len(speedRange), 4, 4))
        B = np.zeros((len(speedRange), 4, 2))

        for i, speed in enumerate(speedRange):
            A[i], B[i] = self.state_space(speed)

        d = {}

        d['Speed'] = speedRange

        for i in range(2, 4):
            for j in range(4):
                col = 'a' + str(i + 1) + str(j + 1)
                d[col] = A[:, i, j]

        for i in range(2, 4):
            for j in range(2):
                col = 'b' + str(i + 1) + str(j + 1)
                d[col] = B[:, i, j]

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
        self.set_default_parameters()

    def set_default_parameters(self):
        for k in self.parameters.keys():
            self.parameters[k] = self.defaultParameters[k]

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
        B : ndarray, shape(4,2)
            The input matrix with inputs [steer torque, lateral force].

        """
        # the B matrix returned is for the inputs [roll torque, steer torque]
        A, BT = self.bicycle.state_space(speed, nominal=True)
        if self.rider == 'Jason':
            H = np.array([[0.943], [0.011]])
        else:
            H = np.array([[0.902], [0.011]])
        BF = np.dot(BT[2:, :], H)
        B = np.hstack((BT[:, 1].reshape(4,1), np.vstack((np.zeros((2,1)), BF))))

        return A, B

    def magnitude_phase(self, speed, w):

        A, B = self.state_space(speed)

        C = np.array([[1., 0., 0., 0.],
                      [0., 1., 0., 0.]])
        D = np.zeros((2, 1))

        sys = control.StateSpace(A, B.reshape(4, 1), C, D)
        bode = control.Bode(w, sys)
        mag, phase = bode.mag_phase_system(sys)

        return mag.squeeze(), phase.squeeze()
