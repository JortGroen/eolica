from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
import yaml, munch, os
from pathlib import Path
import matplotlib.pyplot as plt
from py_wake.site.xrsite import GlobalWindAtlasSite
from py_wake.wind_turbines import WindTurbine, WindTurbines
from .turbines import turbine_dict
from utils import utils

class EolicaPark(GlobalWindAtlasSite):
    '''
    this is a class to host the windpark object
    '''

    def __init__(self, yamlfile) -> None: 
        self.config = None
        self.name = None
        self.lats, self.lons, self.alts, self.ttypes, self.tclass = [], [], [], [], []
        self.site, self.turbines = None, None

        self.load_configuration(yamlfile)
        self.load_turbines()
        self.load_site()
        
    def load_configuration(self, yamlfile):
        '''
        loads the yaml file into a data/config dictionary
        '''

        with open(yamlfile, 'r') as file:
            self.config = yaml.safe_load(file)
            self.config = munch.munchify(self.config)

        self.name = self.config.park_name

        ## make the results directory as well
        self.results = Path(os.getcwd()) / 'results' / self.name
        self.results.mkdir(parents=True, exist_ok=True)

        print(f'[] --- eolica: done loading the park configuration')

    def load_turbines(self):
        '''
        this function loads the turbines into a pywake windturbinelist
        '''
        
        for turbine in self.config.turbines:
            self.lats  .append(turbine.location.latitude )
            self.lons  .append(turbine.location.longitude)
            self.alts  .append(turbine.location.altitude )
            self.ttypes.append(turbine.type)
            try:
                self.tclass.append(turbine_dict[turbine.type])
            except KeyError:
                print(f'[] --- ERROR: check the exact turbine type name in your yaml file!')
                print(f'[] --- ERROR: you are trying to load a turbine with name {turbine.type} which is not supported.')
                print(f'[] --- ERROR: available types are: {list(turbine_dict.keys())}')

        self.mean_lat = np.mean(self.lats)
        self.mean_lon = np.mean(self.lons)

        self.latlons = [(i, j) for i,j in zip(self.lats, self.lons)]
        self.xys     = utils.calculate_xy_distances(list(zip(self.lats, self.lons)), meters=True)
        self.xs = [i[0] for i in self.xys]
        self.ys = [i[1] for i in self.xys]
            
        self.turbines = WindTurbines.from_WindTurbine_lst(self.tclass)

        print(f'[] --- eolica: done loading the turbines')

    def load_site(self):
        '''
        loads the site, according to the specs in the yaml
        '''
        if self.config.site_type == 'GlobalWindAtlasSite':
            self.site = GlobalWindAtlasSite(self.mean_lat, self.mean_lon, np.mean(self.alts), self.config.roughness)
            
            ## plot the wind speed and direction thingy
            fig = plt.figure()

            self.site.plot_ws_distribution().plot()
            fig.savefig(self.results / f'{self.name}_ws.png')

            self.site.plot_wd_distribution().plot()
            fig.savefig(self.results / f'{self.name}_wd.png')
        else:
            print(f'[] --- eolica: you did not specify a proper site type!')


        print(f'[] --- eolica: done loading the site')

    def plot_turbines_powerCT(self):
        '''
        this function plots the power-ct curves for each turbine type in the windpark into a 
        turbines/ subdirectory in the results path of the park
        '''
        outdir = self.results / 'turbines'
        outdir.mkdir(exist_ok=True)

        tlist = list(set(self.tclass))
        nrow = int(len(tlist)/2)+1
        fig = plt.figure(figsize=(14,5*nrow))
        for ti, t in enumerate(tlist):
            myint = int(100*nrow + 20 + (ti+1))
            fig.add_subplot(myint).set_ylim(0., 4.5e6)
            t.plot_power_ct()
        plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05, wspace=0.3, hspace=0.3)

        fig.savefig(outdir / 'turbine_types.png', dpi=400)
        fig.savefig(outdir / 'turbine_types.pdf', dpi=400)







    def __repr__(self):
        return f'''EolicaPark(name={self.name}, turbines={self.turbines}, \
                   lat={np.mean(self.lats)}, lon={np.mean(self.lons)}, alt={np.mean(self.alts)})'''
            
        ## turbines = [
        ##     EolicaTurbine(t['number'], t['type'], t['location']['latitude'], t['location']['longitude'])
        ##     for t in data['wind_turbine_park']['turbines']
        ## ]
        ## park = EolicaPark(data['wind_turbine_park']['name'], turbines)

#mysite = EolicaPark('parks/alkmaar.yaml') 