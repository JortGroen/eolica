import numpy as np
import os
import osmnx
import io
import folium
import matplotlib.pyplot as plt

from PIL import Image
from abc import ABC, abstractmethod
from pathlib import Path
from py_wake.site.xrsite import GlobalWindAtlasSite
from py_wake.wind_turbines import WindTurbine, WindTurbines
from .turbines import turbine_dict
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
            self.site = GlobalWindAtlasSite(self.mean_lat, self.mean_lon, np.mean(self.alts), self.config.roughness)
            
            ## plot the wind speed and direction thingy
            fig = plt.figure()

            self.site.plot_ws_distribution().plot()
            fig.savefig(self.results / f'{self.name}_ws.png')

            self.site.plot_wd_distribution().plot()
            fig.savefig(self.results / f'{self.name}_wd.png')
        else:
            print(f'[] --- eolica: you did not specify a proper site type!')


        print(f'[] --- eolica: done loading the site')

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
        plt.title(f'map of {self.name}')
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
                                name = 'Esri Satellite',
                                overlay = False,
                                control = True).add_to(map_osm)

        # add markers for each GPS coordinate
        for tn, lat, lon in zip(self.tnames, self.lats, self.lons):
            myicon = folium.CustomIcon( 'eolica/utils/folium_icons/turbine_tall.png', icon_size=(66, 66))
            folium.Marker(location=[lat, lon], popup=f'{tn}', icon=myicon).add_to(map_osm)

        # save the map as an HTML file
        outfile = self.results / f'{self.name}_map_satellite.html'
        map_osm.save(outfile)

        img_data = map_osm._to_png(2)
        img = Image.open(io.BytesIO(img_data))
        img.save(outfile.with_suffix('.png'))

    def __repr__(self):
        return f'''EolicaPark(name={self.name}, turbines={self.turbines}, \
                   lat={np.mean(self.lats)}, lon={np.mean(self.lons)}, alt={np.mean(self.alts)})'''