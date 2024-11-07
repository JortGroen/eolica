import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import py_wake
from py_wake.literature.gaussian_models import Bastankhah_PorteAgel_2014

class EolicaSimulation():

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

    def specific_ws_wd(self, ws=None, wd=None):
        '''
        simulate a model / park / whatever
        '''
        
        sim_res = self.model(self.park.lats, self.park.lons, 
                             h=self.park.alts,
                             TI=self.park.config.model_parameters['TI'],
                             type = range(len(self.park.tclass)),
                             wd=wd,
                             ws=ws)

        if not ws and not wd:
            ax1, ax2 = plt.subplots(1,2, figsize=(12,4))[1]
            sim_res.Power.sel(wt=1).T.plot(ax=ax1)
            ax1.set_xlabel('wd (deg)')
            ax1.set_ylabel('ws (m/s)')
            ax1.set_title('WT 35')
            self.park.turbines.plot(self.park.lats,self.park.lons, ax=ax2)
            ax2.plot(self.park.lats[1],self.park.lons[1],'or')
            ax2.set_xlabel('x (m)')
            plt.savefig(self.park.results / 'foobar.png', dpi=400)

        return sim_res
        