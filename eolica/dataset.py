import pandas as pd
import numpy as np
from datetime import datetime

class EolicaDataset():

    def __init__(self, config):
        self.config = config
        self.df = None
        self.load_dataset()

    def load_dataset(self):
        '''
        this loads an arbitrary input csv into a somewhat standard dataset that we can use in the simulation
        '''

        infile = self.config.input_data.file

        df = pd.read_csv(infile, parse_dates=[self.config.input_data.features.time])

        ## apply the selections from the yaml file
        for k,v in self.config.input_data.selection.items():
            df = df[df[k] == v]

        ## rename the columns to have standard feature names
        ## just need to invert the dirctionary first
        rename_dict = {v: k for k, v in self.config.input_data.features.items()}
        df = df.rename(columns = rename_dict)

        ## now just select the features we need ...
        df = df[self.config.input_data.features.keys()]
        if self.config.input_data.range:
            start = pd.to_datetime(self.config.input_data.range.start).tz_localize('Europe/Vienna').tz_convert('UTC')
            end   = pd.to_datetime(self.config.input_data.range.end  ).tz_localize('Europe/Vienna').tz_convert('UTC')
            assert end > start, f'[]--- eolica: ERROR: start and end time are not correct start:{start} end: {end}'
            df = df[(df['time'] >= start) & (df['time'] <= end)]

        ## calculate x and y wind speeds for quiver plots
        df['ws_u']  = df['ws'] * np.cos(np.deg2rad( (270. - df['wd']) % 360 )) #.values[start:end]
        df['ws_v']  = df['ws'] * np.sin(np.deg2rad( (270. - df['wd']) % 360 )) #.values[start:end]

        self.df = df