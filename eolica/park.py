from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
import yaml, os
from pathlib import Path
import matplotlib.pyplot as plt
from py_wake.site.xrsite import GlobalWindAtlasSite
from py_wake.wind_turbines import WindTurbine, WindTurbines
from .turbines import turbine_dict


#class EolicaTurbine:
#    def __init__(self, number, type, latitude, longitude):
#        self.number = number
#        self.type = type
#        self.latitude = latitude
#        self.longitude = longitude
#
#    def __repr__(self):
#        return f"EolicaTurbine(number={self.number}, type={self.type}, latitude={self.latitude}, longitude={self.longitude})"

class EolicaPark(GlobalWindAtlasSite):
    '''
    this is a class to host the windpark object
    '''

    def __init__(self, yamlfile) -> None: 
        self.config_fn = yamlfile
        self.config = None
        self.lats, self.lons, self.alts, self.ttypes, self.tclass = [], [], [], [], []
        self.name = None
        self.turbines = None

        self.load_park()
        
    def load_park(self):
        with open(self.config_fn, 'r') as file:
            self.config = yaml.safe_load(file)

        self.name = self.config['park_name']
        for turbine in self.config['turbines']:
            self.lats  .append(turbine['location']['latitude' ])
            self.lons  .append(turbine['location']['longitude'])
            self.alts  .append(turbine['location']['altitude' ])
            self.ttypes.append(turbine['type'])
            try:
                self.tclass.append(turbine_dict[turbine['type']])
            except KeyError:
                print(f'[]--- ERROR: check the exact turbine type name in your yaml file!')
                print(f'[]--- ERROR: you are trying to load a turbine with name {turbine["type"]} which is not supported.')
                print(f'[]--- ERROR: available types are: {list(turbine_dict.keys())}')
            
        self.turbines = WindTurbines.from_WindTurbine_lst(self.tclass)


        ## make the results directory as well
        self.results = Path(os.getcwd()) / 'results' / self.name
        self.results.mkdir(parents=True, exist_ok=True)

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