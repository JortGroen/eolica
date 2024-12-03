import numpy as np
import pandas as pd
import os
import osmnx
import io
import folium
import matplotlib.pyplot as plt

import plotly.express as px
from PIL import Image
from abc import ABC, abstractmethod
from pathlib import Path
from py_wake.site.xrsite import GlobalWindAtlasSite
from py_wake.wind_turbines import WindTurbine, WindTurbines
from .turbines import turbine_dict, turbine_icons
from eolica import utils

class EolicaPark(GlobalWindAtlasSite):
    '''
    this is a class to host the windpark object
    '''

    def __init__(self, yamlfile) -> None: 
        self.config = None
        self.name = None
        self.lats, self.lons, self.alts = [], [], []
        self.ttypes, self.tclass, self.tnames = [], [], []
        self.site, self.turbines = None, None

        self.load_configuration(yamlfile)
        self.load_turbines()
        self.load_site()
        
    def load_configuration(self, yamlfile):
        '''
        loads the yaml file into a data/config dictionary
        '''

        #with open(yamlfile, 'r') as file:
        #    self.config = yaml.safe_load(file)
        #    self.config = munch.munchify(self.config)
        self.config = utils.utils.load_yaml_config(yamlfile)

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
            self.tnames.append(turbine.name)
            try:
                self.tclass.append(turbine_dict[turbine.type])
            except KeyError:
                print(f'[] --- ERROR: check the exact turbine type name in your yaml file!')
                print(f'[] --- ERROR: you are trying to load a turbine with name {turbine.type} which is not supported.')
                print(f'[] --- ERROR: available types are: {list(turbine_dict.keys())}')

        self.mean_lat = np.mean(self.lats)
        self.mean_lon = np.mean(self.lons)
        self.alts = [i-np.min(self.alts) for i in self.alts]

        self.latlons = [(i, j) for i,j in zip(self.lats, self.lons)]
        self.xys     = utils.utils.calculate_xy_distances(list(zip(self.lats, self.lons)), meters=True)
        self.xs = [i[0] for i in self.xys]
        self.ys = [i[1] for i in self.xys]
        self.sizex = max(self.xs)-min(self.xs)
        self.sizey = max(self.ys)-min(self.ys)
            
        self.turbines = WindTurbines.from_WindTurbine_lst(self.tclass)

        print(f'[] --- eolica: done loading the turbines')

    def load_site(self):
        '''
        loads the site, according to the specs in the yaml
        '''
        if self.config.site_type == 'GlobalWindAtlasSite':
            print(f'[] --- eolica: making site {self.name}')
            self.site = GlobalWindAtlasSite(self.mean_lat, self.mean_lon, np.mean(self.alts), self.config.roughness)
        ## ## init the globalwindatlassite
        ## super.__init__(self.xs, self.ys, np.mean(self.alts), self.config.roughness, ti=None)

            
            ## plot the wind speed and direction thingy
            fig = plt.figure()

            self.make_windrose_plot()
            #self.site.plot_ws_distribution().plot()
            #fig.savefig(self.results / f'{self.name}_ws.png')

            # make that plot nicer as well
            #self.site.plot_wd_distribution().plot()
            #fig.savefig(self.results / f'{self.name}_wd.png')
        else:
            print(f'[] --- eolica: you did not specify a proper site type!')


        print(f'[] --- eolica: done loading the site')

    def make_windrose_plot(self):
        '''
        makes a nice plot of a windrose for the given weibull distribution
        '''
        # ranges for the legend of the plot
        ranges = [0., 1., 2., 3., 4., 5., 6., 8., 10., 100.]

        # nicer to have a separate object
        ds = self.site.ds

        # construct the df. calculate the weibull distribution and ranges in the cdf
        data = []
        for _i, sector in enumerate(ds['wd'].values[:12]):
            freq = ds['Sector_frequency'].values[_i]
            freqs, slist = utils.utils.weibull_strengths(ds['Weibull_A'].values[_i], ds['Weibull_k'].values[_i], ranges)
            freqs = [i*freq for i in freqs]
            for _j,s in enumerate(freqs):
                data.append([sector, s*100., slist[_j]])

        # make it into a df for easy plotting
        df  = pd.DataFrame(data, columns=['sectors', 'frequency', 'strength'])

        # the px windrose plot
        fig = px.bar_polar(df, r='frequency', theta='sectors',
               color='strength', template='plotly',
               color_discrete_sequence= px.colors.sequential.Plasma_r)

        fig.update_layout(title=dict(text=f'windrose for park {self.name}',
                                     font=dict(family='Arial',
                                               size=20)))
                          #showlegend=True,
                          #legend=dict(title='legend',
                          #            font=dict(family='Arial',
                          #                      size=14)),


        try:
            fig.write_image(self.results / f'{self.name}_windrose.png')
            fig.write_image(self.results / f'{self.name}_windrose.pdf')
            fig.write_image(self.results / f'{self.name}_windrose.html')
        except Exception as e:
            print(f'[] --- eolica: ERROR saving the windrose plot: {e}')

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


    def plot_windpark_map(self):
        '''
        downloads an OpenStreetMap area, places indicators on the map,
        and saves it as a png file.
        '''

        size = max([self.sizex, self.sizey]) / 2. * 1.2
        # download the map area
        try:
            graph = osmnx.graph_from_point((self.mean_lat, self.mean_lon), dist=size, network_type='all')#, simplify=True)
        except Exception as e:
            print(f'Error downloading OSM data: {e}')
            return

        # Convert graph to a geodataframe of nodes and edges
        nodes, edges = osmnx.graph_to_gdfs(graph)

        # Plot the map
        fig, ax = plt.subplots(figsize=(10, 10))
        edges.plot(ax=ax, linewidth =0.5, color='gray')
        nodes.plot(ax=ax, markersize=0.5, color='blue')

        # Add markers for GPS coordinates
        for tn, lat, lon in zip(self.tnames, self.lats, self.lons):
            ax.plot(lon, lat, marker='*', color='red', markersize=8, label=tn)

        # Save the map to a file
        plt.title(f'map of {self.name} windpark ({self.mean_lat:.4f}° N, {self.mean_lon:.4f}° E)')
        #plt.legend(['objects'], loc='upper right')
        plt.axis('off')
        plt.savefig(self.results / f'{self.name}_map_simple.png', bbox_inches='tight', dpi=300)
        #plt.show()

    def plot_windpark_map_satellite(self):
        '''
        Downloads an OpenStreetMap area, places indicators on the map,
        and saves it as a PNG file.
        '''
        # initialize the map
        map_osm = folium.Map(location=[self.mean_lat, self.mean_lon], zoom_start=14)#width=self.sizex, height=self.sizey)
        tile = folium.TileLayer(tiles = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                                attr = 'Esri',
                                name = 'ESRI satellite imagery',
                                overlay = False,
                                control = True).add_to(map_osm)

        # add markers for each GPS coordinate
        for tn, tt, lat, lon in zip(self.tnames, self.ttypes, self.lats, self.lons):
            myicon = folium.CustomIcon( f'eolica/utils/folium_icons/{turbine_icons[tt]}', icon_size=(66, 66))
            folium.Marker(location=[lat, lon], popup=f'{tn}', icon=myicon).add_to(map_osm)

        # add a toggle of the layers
        folium.LayerControl().add_to(map_osm)

        # save the map as an HTML file
        outfile = self.results / f'{self.name}_map_satellite.html'
        map_osm.save(outfile)

        img_data = map_osm._to_png(2)
        img = Image.open(io.BytesIO(img_data))
        img.save(outfile.with_suffix('.png'))

    def __repr__(self):
        return f'''EolicaPark(name={self.name}, turbines={self.turbines}, \
                   lat={np.mean(self.lats)}, lon={np.mean(self.lons)}, alt={np.mean(self.alts)})'''