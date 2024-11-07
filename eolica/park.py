from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
import yaml, os
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
        self.config  = yamlfile
        self.lats, self.lons, self.alts, self.ttypes, self.tclass = [], [], [], [], []
        self.name = None
        self.turbines = None

        self.load_park()
        
    def load_park(self):
        with open(self.config, 'r') as file:
            data = yaml.safe_load(file)

        self.name = data['park_name']
        for turbine in data['turbines']:
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

    def __repr__(self):
        return f'''EolicaPark(name={self.name}, turbines={self.turbines}, \
                   lat={np.mean(self.lats)}, lon={np.mean(self.lons)}, alt={np.mean(self.alts)})'''
            
        ## turbines = [
        ##     EolicaTurbine(t['number'], t['type'], t['location']['latitude'], t['location']['longitude'])
        ##     for t in data['wind_turbine_park']['turbines']
        ## ]
        ## park = EolicaPark(data['wind_turbine_park']['name'], turbines)

#mysite = EolicaPark('parks/alkmaar.yaml') 