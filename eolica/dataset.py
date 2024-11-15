import pandas as pd
import numpy as np
import os, yaml, munch, json
from datetime import datetime
#from utils import load_yaml_config
from utils import utils

class EolicaDataset():

    def __init__(self, yamlfile):
        self.config = utils.load_yaml_config(yamlfile)
        self.df = None
        self.resolution = None
        self.load_dataset()

    def load_dataset(self):
        if   self.config.simulation.type == 'wind_series':
            self.load_static_series()

        elif self.config.simulation.type == 'redis_message':
            self.load_redis_series()

        else:
            print(f'[] --- eolica: the type of simulation you chose is not supported! options are:')
            print(f'[] --- eolica: [\'wind_series\', \'redis_message\'... ]')
            exit(1)

    def infer_resolution(self, df):
        diff_time = df.index.diff()
        resolutions = diff_time.unique().total_seconds()/60.
        resolutions = resolutions[~np.isnan(resolutions)]
        if len(resolutions) == 1:
            print(f'[] --- eolica: infered the time resolution to be {resolutions[0]} minutes for the entire dataset')
        else:
            print(f'[] --- eolica: found multiple time resolutions in the dataset: {resolutions.values}')

        return resolutions

    def load_static_series(self):
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
        df.set_index('time', inplace=True)
        try:
            ## FIXME this might be an issue with the localization and the conversion to UTC! check!
            print(f'[] --- eolica: selecting range of the timeseries from {self.config.simulation.range.start} to {self.config.simulation.range.end}')
            start = pd.to_datetime(self.config.simulation.range.start).tz_localize('Europe/Vienna').tz_convert('UTC')
            end   = pd.to_datetime(self.config.simulation.range.end  ).tz_localize('Europe/Vienna').tz_convert('UTC')
            assert end > start, f'[] --- eolica: ERROR: start and end time are not correct start:{start} end: {end}'
            df = df[(df['time'] >= start) & (df['time'] <= end)]
        except AttributeError:
            print('[] --- eolica: no range selected')

        ## calculate x and y wind speeds for quiver plots
        df['ws_u']  = df['ws'] * np.cos(np.deg2rad( (270. - df['wd']) % 360 )) #.values[start:end]
        df['ws_v']  = df['ws'] * np.sin(np.deg2rad( (270. - df['wd']) % 360 )) #.values[start:end]
        df['ws_u_norm']  = df['ws_u'] / df['ws']
        df['ws_v_norm']  = df['ws_v'] / df['ws']

        ## make sure we know the time resolution in minutes
        try:
            self.resolution = self.config.simulation.resolution
        except AttributeError:
            self.resolution = self.infer_resolution(df)
            self.resolution = self.resolution.min()
            df = df.resample(pd.to_timedelta(self.resolution, unit='m')).interpolate(method='polynomial', order=3)

        ## now put the dataframe into the df member
        self.df = df

    def load_redis_series(self):
        '''
        this loads a message from the redis stream of the rdp data-crawler into the regular format.
        it also homogenizes the tiem resolution (i'll try to do that generalized for all weatehr forecasts)
        '''

        ## load the redis message
        msg = self.config.simulation.message

        ## sub-select only the relevant information
        selected_dict = {key: json.loads(msg.data[value]) for key,value in self.config.simulation.features.items()}

        ## make the time stamp a datetime object
        selected_dict['time'] = pd.to_datetime(selected_dict['time']) ## convert to datetime

        #assert len(selected_dict['time']) == len(series_ws) == len(series_wd), f'[] --- eolica: ERROR lengths of series from redis are not the same'

        ## make a dataframe out of the dict
        df = pd.DataFrame(selected_dict)
        df.set_index('time', inplace=True)

        ## apply the selections from the yaml file
        try:
            for k,v in self.config.simulation.selection.items():
                df = df[df[k] == v]
            print(f'[] --- eolica: selection applied!')
        except AttributeError:
            print('[] --- eolica: no selection chosen on the simulation input data.')

        try:
            ## FIXME this might be an issue with the localization and the conversion to UTC! check!
            print(f'[] --- eolica: selecting range of the timeseries from {self.config.simulation.range.start} to {self.config.simulation.range.end}')
            start = pd.to_datetime(self.config.simulation.range.start).tz_localize('Europe/Vienna').tz_convert('UTC')
            end   = pd.to_datetime(self.config.simulation.range.end  ).tz_localize('Europe/Vienna').tz_convert('UTC')
            assert end > start, f'[] --- eolica: ERROR: start and end time are not correct start:{start} end: {end}'
            df = df[(df['time'] >= start) & (df['time'] <= end)]
        except AttributeError:
            print('[] --- eolica: no range selected')

        ## make sure we know the time resolution in minutes
        try:
            self.resolution = self.config.simulation.resolution
        except AttributeError:
            self.resolution = self.infer_resolution(df)
            self.resolution = self.resolution.min()
            df = df.resample(pd.to_timedelta(self.resolution, unit='m')).interpolate(method='polynomial', order=3)

        ## calculate x and y wind speeds for quiver plots
        df['ws_u']  = df['ws'] * np.cos(np.deg2rad( (270. - df['wd']) % 360 )) #.values[start:end]
        df['ws_v']  = df['ws'] * np.sin(np.deg2rad( (270. - df['wd']) % 360 )) #.values[start:end]
        df['ws_u_norm']  = df['ws_u'] / df['ws']
        df['ws_v_norm']  = df['ws_v'] / df['ws']

        self.df = df
