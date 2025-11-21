import pandas as pd
import numpy as np
import os, yaml, munch, json
from datetime import datetime
from eolica.utils.utils import load_yaml_config, EolicaConfigError, check_for_gaps

from pathlib import Path

class EolicaDataset():

    def __init__(self, yamlfile, message=None, type='simulation'):
        '''
        this class loads the dataset that is used for the simulation. it can be either a static dataset or a message from the redis stream
        '''
        self.config = load_yaml_config(yamlfile)
        self.message = message
        self.df = None
        self.resolution = None
        self.type = type
        self.load_dataset()

    def load_dataset(self):
        '''
        this function loads the dataset according to the type of simulation that is chosen in the yaml file
        it can be either a static dataset or a message from the redis stream
        or a production dataset which is considered a static dataset
        '''
        
        try:
            if   self.config.simulation.type == 'wind_series' or self.type == 'production':
                if self.message:
                    raise EolicaConfigError(f'do not provide message with static simulation or production config!')
                self.load_static_series()

            elif self.config.simulation.type == 'redis_message':
                self.load_redis_series(self.message)

        except EolicaConfigError as e:
            print(f'[] --- eolica: ERROR {e}')
            print(f'[] --- eolica: the type of simulation you chose is not supported! options are:')
            print(f'[] --- eolica: [\'wind_series\', \'redis_message\'... ]')
            print(f'[] --- eolica: exiting ...')
            exit()
            
    def load_verbund_dataset(self):
        '''
        this function loads a verbund dataset which is ... bad
        '''
        dateformat = ' %d.%m.%Y %H:%M'
        df_prod = pd.read_csv(self.config.production.file, sep=';', decimal=',', thousands='.')
        selected_features = [ i for i in self.config.production.features.values() ]
        df_prod = df_prod[selected_features]
        for k,v in self.config.production.selection.items():
            df_prod = df_prod[df_prod[k] == v]

        #unique_ids = df_prod['Anlage'].unique()
        #dataframes = {id_value: df_prod[df_prod['Anlage'] == id_value].reset_index(drop=True) for id_value in unique_ids}

        df_prod['time'] = pd.to_datetime(df_prod[self.config.production.features.time], format=dateformat)
        df_prod.drop(columns=self.config.production.features.time, inplace=True)
        gaps = check_for_gaps(df_prod, '10min')

        date_range = pd.date_range(df_prod['time'].min(), df_prod['time'].max(), freq='10min') - pd.Timedelta('1h')

        if len(date_range) != len(df_prod['time']):
            print(f'[] --- eolica: found {len(date_range)} dates in the date range and {len(df_prod["time"])} unique dates in the dataset')
        else:
            df_prod['time'] = date_range

        #df_prod['time'] = df_prod['time'].dt.tz_localize('Europe/Vienna', ambiguous='NaT')

        return df_prod

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

        config = self.config.simulation if self.type == 'simulation' else self.config.production

        infile = Path(config.file)
        if not infile.exists():
            print(f'[] --- eolica: ERROR: the file {infile} does not exist!')
            print(f'[] --- eolica: exiting ...')
            exit()

        ## load the dataset
        ## this should be done nicer at some point ... perhaps i should write a prep dataset code somewhere else
        if self.type == 'production' and config.type == 'verbund':
            df = self.load_verbund_dataset()
        else:
            df = pd.read_csv(infile, parse_dates=[config.features.time])

        ## apply the selections from the yaml file
        try:
            for k,v in config.selection.items():
                df = df[df[k] == v]
            print(f'[] --- eolica: selection applied!')
        except AttributeError:
            print('[] --- eolica: no selection chosen on the simulation input data.')


        ## rename the columns to have standard feature names
        ## just need to invert the dirctionary first
        rename_dict = {v: k for k, v in config.features.items()}
        df = df.rename(columns = rename_dict)

        ## now just select the features we need ...
        df = df[config.features.keys()]


        ## convert u and v to wd and ws if it isn't already the case
        df = self.convert_uv_to_wswd(df)

        ## set the time index
        if df['time'].iloc[0].tzinfo is not None: # check if the datetime has a tzinfo
            print('[] --- eolica: found timezone information in the time column, converting to UTC')
        else:
            df['time'] = df['time'].dt.tz_localize('UTC')
        df.set_index('time', inplace=True)
        try:
            ## FIXME this might be an issue with the localization and the conversion to UTC! check!
            print(f'[] --- eolica: selecting range of the timeseries from {config.range.start} to {config.range.end}')
            start = pd.to_datetime(config.range.start).tz_localize('Europe/Vienna').tz_convert('UTC')
            end   = pd.to_datetime(config.range.end  ).tz_localize('Europe/Vienna').tz_convert('UTC')
            assert end > start, f'[] --- eolica: ERROR: start and end time are not correct start:{start} end: {end}'
            # df = df[(df['time'] >= start) & (df['time'] <= end)]
            df = df[(df.index >= start) & (df.index <= end)]
        except AttributeError:
            print('[] --- eolica: no range selected')

        ## calculate x and y wind speeds for quiver plots
        df['ws_u']  = df['ws'] * np.cos(np.deg2rad( (270. - df['wd']) % 360 )) #.values[start:end]
        df['ws_v']  = df['ws'] * np.sin(np.deg2rad( (270. - df['wd']) % 360 )) #.values[start:end]
        df['ws_u_norm']  = df['ws_u'] / df['ws']
        df['ws_v_norm']  = df['ws_v'] / df['ws']

        ## make sure we know the time resolution in minutes
        try:
            self.resolution = config.resolution
        except AttributeError:
            self.resolution = self.infer_resolution(df)
            self.resolution = self.resolution.min()
            df = df.resample(pd.to_timedelta(self.resolution, unit='m')).interpolate(method='polynomial', order=3)

        ## now put the dataframe into the df member
        self.df = df

    def convert_uv_to_wswd(self, df):
        '''
        helper function that converts u and v components of the wind into ws and wd which is used in pywake
        '''

        if   all([i in df.columns for i in ['ws', 'wd']]):
            print('[] --- eolica: found "ws" and "wd" in the dataframe!')
        elif all([i in df.columns for i in ['wu', 'wv']]):
            print('[] --- eolica: found "wu" and "wv" in the dataframe, converting to "ws" and "wd"')
            df['ws'] = np.sqrt(df['wu']**2 + df['wv']**2)
            df['wd'] = (270. - np.arctan2(df['wv'], df['wu']) * 180 / np.pi) % 360
        else:
            print('[] --- eolica: ERROR!!! there is neither ("wd", "ws"), nor ("wu", "wv") in the dataset!')
            print('[] --- eolica: ERROR!!! exiting')
            exit()

        return df

    def load_redis_series(self, message):
        '''
        this loads a message from the redis stream of the rdp data-crawler into the regular format.
        it also homogenizes the tiem resolution (i'll try to do that generalized for all weatehr forecasts)
        '''

        ## sub-select only the relevant information
        selected_dict = {key: json.loads(message[value]) for key,value in self.config.simulation.features.items()}

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
