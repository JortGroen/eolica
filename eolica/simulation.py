import pandas as pd
import numpy as np
import py_wake
from py_wake.literature.gaussian_models import Bastankhah_PorteAgel_2014

class Simulation():

    def __init__(self, park, series=None):
        self.park = park
        self.series = series

        self.model = None
        self.make_simulation_model()

    def make_simulation_model(self):
        '''
        this makes the simulation model with the park and specs from the yaml
        '''
        modelname = self.park.config.model_type
        if modelname == 'Bastankhah_PorteAgel_2014':

            self.model = Bastankhah_PorteAgel_2014(self.park.site, self.park.turbines, k=self.park.config.model_parameters['k'])

        else:
            print(f'[]--- eolica: ERROR: you did not specify a good wind forecasting model!')

        print(f'[]--- eolica: done making the simulation model {modelname}')

    def specific_ws_wd(self, ws, wd):
        '''
        simulate a model / park / whatever
        '''
        pass
        