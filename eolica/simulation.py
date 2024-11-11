import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import py_wake
from py_wake.literature.gaussian_models import Bastankhah_PorteAgel_2014
from utils import AIT_COLORS

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
            print(f'[]--- eolica: ERROR: you did not specify a proper wind forecasting model!')
            print(f'[]--- eolica: options are: [Bastankhah_PorteAgel_2014,]')
            exit(1)

        print(f'[]--- eolica: done making the simulation model {modelname}')

    def specific_ws_wd(self, ws=None, wd=None):
        '''
        simulate a model / park / whatever
        '''
        
        sim_res = self.model(self.park.xs, self.park.ys, 
                             h=self.park.alts,
                             TI=self.park.config.model_parameters['TI'],
                             type = range(len(self.park.tclass)),
                             wd=wd,
                             ws=ws)

        if not ws and not wd:
            _color = AIT_COLORS['bordeaux']
            for it,t in enumerate(self.park.ttypes):
                fig, axs = plt.subplots(2,2, figsize=(13,13))
                sim_res.Power.sel(wt=it).T.plot(ax=axs[0, 0], cmap='PuBu_r')
                axs[0, 0].set_xlabel('wd (deg)')
                axs[0, 0].set_ylabel('ws (m/s)')
                axs[0, 0].set_title(f'turbine {it}')

                self.park.turbines.plot(self.park.xs, self.park.ys  , ax=axs[0, 1])
                axs[0, 1].plot(self.park.xs[it],self.park.ys  [it], color=_color, marker='*')
                axs[0, 1].set_xlabel('x (m)')
                axs[0, 1].set_xlim(min(self.park.xs)-200., max(self.park.xs)+200.)
                axs[0, 1].set_ylabel('y (m)')
                axs[0, 1].set_ylim(min(self.park.ys)-200., max(self.park.ys)+200.)

                self.park.turbines.plot(self.park.xs, self.park.alts, ax=axs[1, 0])
                axs[1, 0].plot(self.park.xs[it],self.park.alts[it], color=_color, marker='*')
                axs[1, 0].set_xlabel('x (m)')
                axs[1, 0].set_xlim(min(self.park.xs)-200., max(self.park.xs)+200.)
                axs[1, 0].set_ylabel('z (m)')
                axs[1, 0].set_ylim(0., 300.)

                self.park.turbines.plot(self.park.ys, self.park.alts, ax=axs[1, 1])
                axs[1, 1].plot(self.park.ys[it],self.park.alts[it], color=_color, marker='*')
                axs[1, 1].set_xlabel('y (m)')
                axs[1, 1].set_xlim(min(self.park.ys)-200., max(self.park.ys)+200.)
                axs[1, 1].set_ylabel('z (m)')
                axs[1, 1].set_ylim(0., 300.)

                ## save the figures
                fig.savefig(self.park.results / f'turbines/profile_windturbine_{it}.pdf', dpi=400)
                fig.savefig(self.park.results / f'turbines/profile_windturbine_{it}.png', dpi=400)

                ## the following code doesn't work ... something inside py_wake
                #self.park.turbines.plot_yz(self.park.ys, z=self.park.alts, ax=axs[1, 1])
                #axs[1, 1].plot(self.park.ys[it],self.park.alts[it], color=_color, marker='*')
                ## axs[1, 1].set_xlabel('y (m)')
                ## axs[1, 1].set_xlim(min(self.park.ys)-200., max(self.park.ys)+200.)
                ## axs[1, 1].set_ylabel('z (m)')
                ## axs[1, 1].set_ylim(0., 300.)

        return sim_res
        