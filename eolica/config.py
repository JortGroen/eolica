from pydantic import BaseModel
from typing import Optional, List, Union
from pathlib import Path
from json import dump
import os

class ParkConfig(BaseModel):
    '''
    configuration file for a park
    '''

    # first some information on the park and turbines
    parkname: str  # name of the network
    turbines: dict

    results_path: str = None
    parallel: bool = False
    config: str = None
    simulation: str = None


    def print_config(self):
        '''
        function to print the configuration, for clarity
        '''
    
        print('EƎ--- eolica: printing the park configuration file')
        for k,v in self.model_dump().items():
            print(f'EƎ--- eolica: config: {k:15s}: {str(v)}')

    def save_config(self):
        '''
        save the simulation configuration
        '''

        ## make the absolute paths of the simulation and the config file for convenience
        fn_cfg = 'config_'    +self.parkname+'.json'
        fn_sim = 'simulation_'+self.parkname+'.csv'

        self.config     = os.path.abspath(os.path.join(self.results_path, self.parkname, fn_cfg))
        self.simulation = os.path.abspath(os.path.join(self.results_path, self.parkname, fn_sim))

        outpath = os.path.join(self.results_path, self.parkname)

        if not os.path.isdir(outpath):
            os.makedirs(outpath)
        
        #with open(os.path.join(outpath, outname), "w") as f:
        with open(self.config, "w") as f:
            dump(self.model_dump(), f, indent=2)