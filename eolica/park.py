import numpy as np
import pandas as pd
import os
import osmnx
import io
import folium
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import xarray as xr

import plotly.express as px
from PIL import Image
from abc import ABC, abstractmethod
from pathlib import Path
from py_wake.site.xrsite import GlobalWindAtlasSite, UniformWeibullSite
from py_wake.site import XRSite
from py_wake.site.shear import PowerShear
from py_wake.wind_turbines import WindTurbine, WindTurbines
from .turbines import turbine_dict, turbine_icons
from eolica import utils
from eolica.utils.utils import EolicaConfigError

class EolicaPark(GlobalWindAtlasSite):
    '''
    this is a class to host the windpark object
    '''

    def __init__(self, park_config_file: str = None, turbine_config_file: str = None) -> None: 
        # Safety check: park_config_file is required
        if park_config_file is None or park_config_file == '':
            raise EolicaConfigError('park_config_file is required. Please provide a valid park configuration file path.')
        
        self.config = None
        self.name = None
        self.lats, self.lons, self.alts = [], [], []
        self.ttypes, self.tclass, self.tnames = [], [], []
        self.hub_heights, self.rotor_diameters, self.max_powers = [], [], []
        self.site, self.turbines = None, None
        self.turbine_config_file = turbine_config_file
        self.turbine_config = None
        self.turbine_type_icons = {}  # Mapping for custom turbine icons

        self.load_configuration(park_config_file)
        if self.turbine_config_file:
            self.load_turbine_configuration(self.turbine_config_file)
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

    def load_turbine_configuration(self, yamlfile):
        '''
        loads the turbine configuration yaml file into a dictionary
        '''
        self.turbine_config = utils.utils.load_yaml_config(yamlfile)
        # Build a mapping of turbine types to icons for custom turbines
        self._build_turbine_icon_mapping()
        print(f'[] --- eolica: done loading the turbine configuration')
    
    def _build_turbine_icon_mapping(self):
        '''
        Builds a mapping of turbine types to icons, ensuring each type gets a unique icon.
        First tries to match with existing turbine_icons, then assigns unique icons from available pool.
        '''
        if not self.turbine_config or not hasattr(self.turbine_config, 'turbine_types'):
            return
        
        # Available icon files (excluding the default one)
        available_icons = [
            'turbine_red.png', 'turbine_green.png', 'turbine_pinkish.png', 
            'turbine_tall.png', 'turbine_lightblue.png', 'turbine_yellow.png',
            'turbine_dark.png', 'turbine_light.png', 'turbine_opaque.png',
            'turbine_rby.png'
        ]
        
        # Create a case-insensitive lookup dictionary from turbine_icons
        icon_lookup = {k.lower(): v for k, v in turbine_icons.items()}
        
        # Track which icons have been assigned
        used_icons = set()
        self.turbine_type_icons = {}
        
        # First pass: try to match with existing turbine_icons (case-insensitive)
        for turbine_type_name in self.turbine_config.turbine_types.keys():
            turbine_type_lower = turbine_type_name.lower()
            
            # Try exact match first
            if turbine_type_lower in icon_lookup:
                icon_file = icon_lookup[turbine_type_lower]
                self.turbine_type_icons[turbine_type_name] = icon_file
                self.turbine_type_icons[turbine_type_lower] = icon_file  # Also store lowercase version
                used_icons.add(icon_file)
            else:
                # Try partial match (e.g., "alkmaar_2p3MW" matches "alkmaar_2p3MW")
                matched = False
                for key, icon_file in icon_lookup.items():
                    # Check if turbine type contains key or vice versa (normalized)
                    if (turbine_type_lower.replace('_', '').replace('-', '') == 
                        key.replace('_', '').replace('-', '') or
                        turbine_type_lower.startswith(key.split('_')[0]) or
                        key.startswith(turbine_type_lower.split('_')[0])):
                        self.turbine_type_icons[turbine_type_name] = icon_file
                        self.turbine_type_icons[turbine_type_lower] = icon_file
                        used_icons.add(icon_file)
                        matched = True
                        break
                
                if not matched:
                    # Assign a unique icon from available pool
                    for icon_file in available_icons:
                        if icon_file not in used_icons:
                            self.turbine_type_icons[turbine_type_name] = icon_file
                            self.turbine_type_icons[turbine_type_lower] = icon_file
                            used_icons.add(icon_file)
                            break
                    else:
                        # If all icons are used, cycle through them
                        icon_file = available_icons[len(used_icons) % len(available_icons)]
                        self.turbine_type_icons[turbine_type_name] = icon_file
                        self.turbine_type_icons[turbine_type_lower] = icon_file

    def load_turbines(self):
        '''
        this function loads the turbines into a pywake windturbinelist
        '''
        
        # If turbine_config_file is provided, create turbines dynamically from config
        if self.turbine_config_file and self.turbine_config:
            # Create a dictionary to store turbine types from config file
            turbine_type_dict = {}
            
            # Load turbine types from config file
            for turbine_type_name, turbine_spec in self.turbine_config.turbine_types.items():
                # Convert turbine type name to lowercase for matching (e.g., "Alkmaar_2p3MW" -> "alkmaar_2p3mw")
                turbine_type_key = turbine_type_name.lower()
                
                # Get power and thrust curves
                binning = np.array(turbine_spec.binning)
                power_curve = np.array(turbine_spec.power_curve)
                thrust_curve = np.array(turbine_spec.thrust_curve)
                
                # Convert power curve to W for py_wake (unit is specified in config)
                if hasattr(turbine_spec, 'unit') and turbine_spec.unit == 'kW':
                    # Power curve is in kW, convert to W for py_wake
                    power_curve_w = power_curve * 1000.0
                else:
                    # Assume it's already in W if unit is not specified or is 'W'
                    power_curve_w = power_curve
                
                # Create power curve array in format [wind_speed, power]
                pc_array = np.column_stack([binning, power_curve_w])
                
                # Create thrust curve array (ct values correspond to binning)
                ct_array = np.column_stack([binning, thrust_curve])
                
                # Create a dynamic WindTurbine class for this turbine type
                # We'll create instances with hub_height and diameter from park config
                turbine_type_dict[turbine_type_key] = {
                    'pc_array': pc_array,
                    'ct_array': ct_array,
                    'name': turbine_type_name
                }
            
            # Now create WindTurbine instances for each turbine in the park
            for turbine in self.config.turbines:
                self.lats.append(turbine.location.latitude)
                self.lons.append(turbine.location.longitude)
                self.alts.append(turbine.location.altitude)
                self.ttypes.append(turbine.type)
                self.tnames.append(turbine.name)
                
                # Get hub_height and rotor_diameter from park config (per turbine)
                hub_height = getattr(turbine, 'hub_height', None)
                rotor_diameter = getattr(turbine, 'rotor_diameter', None)
                
                # Convert turbine type to lowercase for matching
                turbine_type_key = turbine.type.lower()
                
                if turbine_type_key in turbine_type_dict:
                    # Get the turbine spec from config
                    spec = turbine_type_dict[turbine_type_key]
                    
                    # Check if hub_height and rotor_diameter are provided
                    if hub_height is None or rotor_diameter is None:
                        raise EolicaConfigError(
                            f'Turbine {turbine.name} (type: {turbine.type}) requires hub_height and rotor_diameter '
                            f'in the park configuration file when using turbine_config_file.'
                        )
                    
                    # Calculate maximum rated power from power curve (in W)
                    max_power_w = np.max(spec['pc_array'][:, 1])
                    
                    # Store turbine dimensions and power
                    self.hub_heights.append(hub_height)
                    self.rotor_diameters.append(rotor_diameter)
                    self.max_powers.append(max_power_w / 1e6)  # Convert to MW for display
                    
                    # Create WindTurbine instance with curves and dimensions from config
                    from py_wake.wind_turbines.power_ct_functions import PowerCtTabular
                    power_ct_func = PowerCtTabular(
                        spec['pc_array'][:, 0],  # wind speeds
                        spec['pc_array'][:, 1],  # power in W
                        'w',
                        spec['ct_array'][:, 1],  # thrust coefficients
                        method='linear'
                    )
                    
                    # Create a WindTurbine instance
                    wt = WindTurbine(
                        name=turbine.type,
                        diameter=rotor_diameter,
                        hub_height=hub_height,
                        powerCtFunction=power_ct_func
                    )
                    
                    self.tclass.append(wt)
                else:
                    raise EolicaConfigError(
                        f'Turbine type "{turbine.type}" not found in turbine_config_file. '
                        f'Available types: {list(turbine_type_dict.keys())}'
                    )
        else:
            # Original behavior: use turbine_dict from turbines.py
            for turbine in self.config.turbines:
                self.lats.append(turbine.location.latitude)
                self.lons.append(turbine.location.longitude)
                self.alts.append(turbine.location.altitude)
                self.ttypes.append(turbine.type)
                self.tnames.append(turbine.name)
                
                # Get hub_height and rotor_diameter from park config if available
                hub_height = getattr(turbine, 'hub_height', None)
                rotor_diameter = getattr(turbine, 'rotor_diameter', None)
                
                try:
                    wt = turbine_dict[turbine.type]
                    self.tclass.append(wt)
                    
                    # Store turbine dimensions (use from config if available, otherwise from turbine object)
                    if hub_height is not None:
                        self.hub_heights.append(hub_height)
                    else:
                        self.hub_heights.append(wt.hub_height())
                    
                    if rotor_diameter is not None:
                        self.rotor_diameters.append(rotor_diameter)
                    else:
                        self.rotor_diameters.append(wt.diameter())
                    
                    # Calculate maximum rated power (in MW)
                    # Get power at high wind speed (20 m/s) as approximation of rated power
                    max_power_w = wt.power(20.0)
                    self.max_powers.append(max_power_w / 1e6)  # Convert to MW for display
                    
                except KeyError:
                    print(f'[] --- ERROR: check the exact turbine type name in your yaml file!')
                    print(f'[] --- ERROR: you are trying to load a turbine with name {turbine.type} which is not supported.')
                    print(f'[] --- ERROR: available types are: {list(turbine_dict.keys())}')
                    # Add None values to keep lists in sync
                    self.hub_heights.append(None)
                    self.rotor_diameters.append(None)
                    self.max_powers.append(None)

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
            try:
                self.site = GlobalWindAtlasSite(self.mean_lat, self.mean_lon, np.mean(self.alts), self.config.roughness)
                ## ## init the globalwindatlassite
                ## super.__init__(self.xs, self.ys, np.mean(self.alts), self.config.roughness, ti=None)

            except Exception as e:
                #wd = np.linspace(0, 360, len(f), endpoint=False)
                #self.site = XRSite(ds=xr.Dataset(data_vars={'WS': 10, 'P': ('wd', f), 'TI': ti}, coords={'wd': wd}), shear=PowerShear(h_ref=100, alpha=.2))
                print(f'[] --- eolica: ERROR: GlobalWindAtlasSite not working!!')
                print(f'                      {e}')
                print(f'[] --- eolica: making a UniformWeibullSite instead!')

                ## make a weibull distributed site with weibull factors:
                ##f = [0.036, 0.039, 0.052, 0.07, 0.084, 0.064, 0.086, 0.118, 0.152, 0.147, 0.1, 0.052]
                ##A = [9.177, 9.782, 9.532, 9.91, 10.043, 9.594, 9.584, 10.515, 11.399, 11.687, 11.637, 10.088]
                ##k = [2.393, 2.447, 2.412, 2.592, 2.756, 2.596, 2.584, 2.549, 2.471, 2.607, 2.627, 2.326]
                ##wd = np.linspace(0, 360, len(f), endpoint=False)
                ##ti = .1
                ##self.site = XRSite(ds=xr.Dataset(data_vars={'Sector_frequency': ('wd', f), 'Weibull_A': ('wd', A), 'Weibull_k': ('wd', k), 'TI': ti}, coords={'wd': wd}))

                self.site = UniformWeibullSite(p_wd = [.20,.25,.35,.25],                         # sector frequencies
                                                  a = [9.176929,  9.782334,  9.531809,  9.909545],  # Weibull scale parameter
                                                  k = [2.392578, 2.447266, 2.412109, 2.591797],     # Weibull shape parameter
                                                  ti = 0.1                                          # turbulence intensity, optional
                                               )
        else:
            print(f'[] --- eolica: you did not specify a proper site type!')


        print(f'[] --- eolica: done loading the site')

    def plot_weibull_dists(self):
        '''
        makes the distributions of the weibull functions for each of the sectors
        '''
        # nicer to have a separate object
        ds = self.site.ds
        sectors = ds.wd.values[:12]
        x = np.linspace(0, 15, 500)

        colors = cm.tab20b(np.linspace(0, 1, len(sectors)))

        fig = plt.figure(figsize=(10, 6))

        for sector, color in zip(sectors, colors):
            Weibull_A = ds.sel(wd=sector).Weibull_A.item()
            Weibull_k = ds.sel(wd=sector).Weibull_k.item()
            y = utils.utils.weibull(x, Weibull_k, Weibull_A)
            y = y *100. * ds.sel(wd=sector).Sector_frequency.item()
            plt.plot(x, y, label=f"sector {int(sector)}°", color=color)

        plt.xlabel('wind speed (m/s)')
        plt.ylabel('probability (%)')
        plt.title(f'Weibull distributions for windpark {self.name}', loc='left')
        plt.legend()
        plt.grid(True)

        fig.savefig(self.results / f'{self.name}_weibull.png')
        fig.savefig(self.results / f'{self.name}_weibull.pdf')

    def plot_windrose(self):
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
               color_discrete_sequence=px.colors.sequential.Plasma_r)

        fig.update_layout(title=dict(text=f'windrose for park {self.name}',
                                     font=dict(family='Arial',
                                               size=20)),
                          showlegend=True,
                          legend=dict(title='windspeed (m/s)',
                                      font=dict(family='Arial',
                                                size=14)))


        try:
            fig.write_image(self.results / f'{self.name}_windrose.png')
            fig.write_image(self.results / f'{self.name}_windrose.pdf')
            fig.write_html (self.results / f'{self.name}_windrose.html')
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
        nrow = int(len(tlist)/2)+len(tlist)%2
        fig = plt.figure(figsize=(14 if len(tlist) > 1 else 7,5*nrow))
        for ti, t in enumerate(tlist):
            myint = int(100*nrow + 20 + (ti+1))
            if len(tlist) > 1:
                fig.add_subplot(myint).set_ylim(0., 4.5e6)

            axs = t.plot_power_ct()
            line0 = axs[0].get_lines()[0]
            line0.set_linewidth(2)
            line0.set_color(utils.utils.AIT_COLORS['bordeaux'])
            axs[0].set_xlabel(axs[0].get_xlabel().replace('[','(').replace(']',')'))
            axs[0].set_ylabel(axs[0].get_ylabel().replace('[','(').replace(']',')'), fontsize=12, color=line0.get_color())
            axs[0].tick_params(axis='y', colors=line0.get_color())
            axs[0].set_ylim(bottom=0)
            
            line1 = axs[1].get_lines()[0]
            line1.set_color(utils.utils.AIT_COLORS['turkis'])
            line1.set_linewidth(2)
            axs[1].set_ylim([0., 1.])
            axs[1].set_ylabel(axs[1].get_ylabel(), fontsize=12, color=line1.get_color())
            axs[1].tick_params(axis='y', colors=line1.get_color())
            axs[1].set_ylim(bottom=0)

        if len(tlist) > 1:
            plt.subplots_adjust(left=0.05, right=0.95, top=0.90, bottom=0.10, wspace=0.3, hspace=0.3)

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
        for i, (tn, tt, lat, lon) in enumerate(zip(self.tnames, self.ttypes, self.lats, self.lons)):
            # Use different icon for each turbine type
            # First try custom turbine icon mapping (for turbines loaded from config)
            if hasattr(self, 'turbine_type_icons') and self.turbine_type_icons:
                # Try exact match first
                icon_file = self.turbine_type_icons.get(tt)
                # Try lowercase match
                if icon_file is None:
                    icon_file = self.turbine_type_icons.get(tt.lower())
                # Try original turbine_icons as fallback
                if icon_file is None:
                    icon_file = turbine_icons.get(tt)
                # Final fallback
                if icon_file is None:
                    icon_file = 'turbine_lightblue.png'
            else:
                # Use standard turbine_icons lookup
                icon_file = turbine_icons.get(tt, 'turbine_lightblue.png')
            
            myicon = folium.CustomIcon( f'eolica/utils/folium_icons/{icon_file}', icon_size=(66, 66))
            
            # Create rich popup with turbine information
            hub_h = self.hub_heights[i] if i < len(self.hub_heights) else None
            rotor_d = self.rotor_diameters[i] if i < len(self.rotor_diameters) else None
            max_p = self.max_powers[i] if i < len(self.max_powers) else None
            
            # Build popup HTML content
            popup_html = f'<div style="font-family: Arial, sans-serif;">'
            popup_html += f'<h3 style="margin-top: 0; margin-bottom: 10px;">{tn}</h3>'
            popup_html += f'<table style="border-collapse: collapse; width: 100%;">'
            
            if tt:
                popup_html += f'<tr><td style="padding: 5px; font-weight: bold;">Type:</td><td style="padding: 5px;">{tt}</td></tr>'
            if hub_h is not None:
                popup_html += f'<tr><td style="padding: 5px; font-weight: bold;">Hub Height:</td><td style="padding: 5px;">{hub_h:.1f} m</td></tr>'
            if rotor_d is not None:
                popup_html += f'<tr><td style="padding: 5px; font-weight: bold;">Rotor Diameter:</td><td style="padding: 5px;">{rotor_d:.1f} m</td></tr>'
            if max_p is not None:
                popup_html += f'<tr><td style="padding: 5px; font-weight: bold;">Rated Power:</td><td style="padding: 5px;">{max_p:.2f} MW</td></tr>'
            
            popup_html += f'</table></div>'
            
            popup = folium.Popup(popup_html, max_width=300)
            folium.Marker(location=[lat, lon], popup=popup, icon=myicon).add_to(map_osm)

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