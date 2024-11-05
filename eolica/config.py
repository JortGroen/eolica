from pydantic import BaseModel
from typing import Optional, List, Union
from pathlib import Path
from json import dump
import os, yaml

class EolicaTurbine:
    def __init__(self, number, type, latitude, longitude):
        self.number = number
        self.type = type
        self.latitude = latitude
        self.longitude = longitude

    def __repr__(self):
        return f"EolicaTurbine(number={self.number}, type={self.type}, latitude={self.latitude}, longitude={self.longitude})"

class EolicaPark:
    def __init__(self, name, turbines):
        self.name = name
        self.turbines = turbines

    def __repr__(self):
        return f"EolicaPark(name={self.name}, turbines={self.turbines})"

def load_config(file_path):
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
    
    turbines = [
        EolicaTurbine(t['number'], t['type'], t['location']['latitude'], t['location']['longitude'])
        for t in data['wind_turbine_park']['turbines']
    ]
    park = EolicaPark(data['wind_turbine_park']['name'], turbines)
    return park

# Example usage
config = load_config('parks/alkmaar.yaml')
print(config)


#class ParkConfig(BaseModel):
#    '''
#    configuration file for a park
#    '''
#
#    # first some information on the park and turbines
#    parkname: str  # name of the network
#    turbines: dict # the turbines are a dict of turbines ... not sure if this works
#
#    results_path: str = None
#    parallel: bool = False
#    config: str = None
#    simulation: str = None
#
#
#    def print_config(self):
#        '''
#        function to print the configuration, for clarity
#        '''
#    
#        print('[]--- eolica: printing the park configuration file')
#        for k,v in self.model_dump().items():
#            print(f'[]--- eolica: config: {k:15s}: {str(v)}')
#
#    def save_config(self):
#        '''
#        save the simulation configuration
#        '''
#
#        ## make the absolute paths of the simulation and the config file for convenience
#        fn_cfg = 'config_'    +self.parkname+'.json'
#        fn_sim = 'simulation_'+self.parkname+'.csv'
#
#        self.config     = os.path.abspath(os.path.join(self.results_path, self.parkname, fn_cfg))
#        self.simulation = os.path.abspath(os.path.join(self.results_path, self.parkname, fn_sim))
#
#        outpath = os.path.join(self.results_path, self.parkname)
#
#        if not os.path.isdir(outpath):
#            os.makedirs(outpath)
#        
#        #with open(os.path.join(outpath, outname), "w") as f:
#        with open(self.config, "w") as f:
#            dump(self.model_dump(), f, indent=2)