import pandas as pd
import numpy as np
from datetime import datetime

class EolicaDataset():

    def __init__(self, config):
        self.config = config
        self.df = None
        self.resolution = None
        self.load_dataset()

        

    def load_dataset(self):
        if self.config.simulation.type == 'wind_series':
            self.load_simple_series()
        else:
            print(f'[] --- eolica: the type of simulation you chose is not supported! options are:')
            print(f'[] --- eolica: [\'wind_series\', ... ]')
            exit(1)

    def load_simple_series(self):
        '''
        this loads an arbitrary input csv into a somewhat standard dataset that we can use in the simulation
        '''

        infile = self.config.simulation.file

        df = pd.read_csv(infile, parse_dates=[self.config.simulation.features.time])

        ## apply the selections from the yaml file
        try:
            for k,v in self.config.simulation.selection.items():
                df = df[df[k] == v]
            print(f'[] --- eolica: selection applied!')
        except AttributeError:
            print('[] --- eolica: no selection chosen on the simulation input data.')


        ## rename the columns to have standard feature names
        ## just need to invert the dirctionary first
        rename_dict = {v: k for k, v in self.config.simulation.features.items()}
        df = df.rename(columns = rename_dict)

        ## now just select the features we need ...
        df = df[self.config.simulation.features.keys()]
        if self.config.simulation.range:
            ## FIXME this might be an issue with the localization and the conversion to UTC! check!
            print(f'[] --- eolica: selecting range of the timeseries from {self.config.simulation.range.start} to {self.config.simulation.range.end}')
            start = pd.to_datetime(self.config.simulation.range.start).tz_localize('Europe/Vienna').tz_convert('UTC')
            end   = pd.to_datetime(self.config.simulation.range.end  ).tz_localize('Europe/Vienna').tz_convert('UTC')
            assert end > start, f'[] --- eolica: ERROR: start and end time are not correct start:{start} end: {end}'
            df = df[(df['time'] >= start) & (df['time'] <= end)]

        ## calculate x and y wind speeds for quiver plots
        df['ws_u']  = df['ws'] * np.cos(np.deg2rad( (270. - df['wd']) % 360 )) #.values[start:end]
        df['ws_v']  = df['ws'] * np.sin(np.deg2rad( (270. - df['wd']) % 360 )) #.values[start:end]

        self.df = df

        ## make sure we know the time resolution in minutes
        try:
            self.resolution = self.config.simulation.resolution
        except AttributeError:
            self.infer_resolution()

    def infer_resolution(self):
        diff_time = self.df['time'].diff()
        self.resolution = diff_time.min().total_seconds() / 60.
        print(f'[] --- eolica: infered the time resolution to be {self.resolutoin} minutes')