from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
import yaml, os
from py_wake.site.xrsite import GlobalWindAtlasSite
from py_wake.wind_turbines import WindTurbine, WindTurbines


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
        self.lats, self.lons, self.alts, self.ttypes = [], [], [], []

        self.load_park()
        
    def load_park(self):
        with open(self.config, 'r') as file:
            data = yaml.safe_load(file)

        for turbine in data['turbines']:
            self.lats.append(turbine['latitude' ])
            self.lons.append(turbine['longitude'])
            self.alts.append(turbine['altitude' ])
            
            
        ## turbines = [
        ##     EolicaTurbine(t['number'], t['type'], t['location']['latitude'], t['location']['longitude'])
        ##     for t in data['wind_turbine_park']['turbines']
        ## ]
        ## park = EolicaPark(data['wind_turbine_park']['name'], turbines)
        return data

mysite = EolicaPark('parks/alkmaar.yaml') 