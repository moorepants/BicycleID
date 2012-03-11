import os

PATH_TO_BDP = "/media/Data/Documents/School/UC Davis/Bicycle Mechanics/BicycleDataProcessor/"
PATH_TO_DATABASE = os.path.join(PATH_TO_BDP, 'InstrumentedBicycleData.h5')
PATH_TO_CORRUPT = os.path.join(PATH_TO_BDP, 'data-corruption.csv')
PATH_TO_BP = "/media/Data/Documents/School/UC Davis/Bicycle Mechanics/BicycleParameters/"
PATH_TO_PARAMETERS = os.path.join(PATH_TO_BP, 'data')
PATH_TO_BD = "/media/Data/Documents/School/UC Davis/Bicycle Mechanics/BicycleDAQ/"
PATH_TO_H5 = os.path.join(PATH_TO_BD, 'data/h5/')
PATH_TO_BS = "/media/Data/Documents/School/UC Davis/Bicycle Mechanics/BicycleSystemID/"
#PATH_TO_SYSTEM_ID_DATA = os.path.join(PATH_TO_BS, 'scripts', 'whipple_grey_fit.mat')
#PATH_TO_SYSTEM_ID_DATA = os.path.join(PATH_TO_BS, 'scripts', 'whipple_grey_fit-noise.mat')
#PATH_TO_SYSTEM_ID_DATA = os.path.join(PATH_TO_BS, 'scripts',
        #'whipple-structured-results-x0-K-freeones-phi.mat')
#PATH_TO_SYSTEM_ID_DATA = os.path.join(PATH_TO_BS, 'scripts',
    #'whipple-structured-results-x0-K.mat')
PATH_TO_SYSTEM_ID_DATA = os.path.join(PATH_TO_BS, 'scripts',
        'whipple-structured-results.mat')
