import math
import numpy as np

def lat_lon_to_cartesian(lat, lon):
    # Convert latitude and longitude to radians
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    
    # Radius of the Earth in km
    R = 6371.0
    
    x = R * lon_rad * math.cos(lat_rad)
    y = R * lat_rad
    return x, y

def calculate_central_point(coords):
    lat_mean = sum(lat for lat, lon in coords) / len(coords)
    lon_mean = sum(lon for lat, lon in coords) / len(coords)
    return lat_mean, lon_mean

def calculate_xy_distances(coords, meters=False):
    central_lat, central_lon = calculate_central_point(coords)
    central_x, central_y = lat_lon_to_cartesian(central_lat, central_lon)
    xy_distances = []
    for lat, lon in coords:
        x, y = lat_lon_to_cartesian(lat, lon)
        distance_x = x - central_x
        distance_y = y - central_y
        if meters:
            distance_x*=1000.
            distance_y*=1000.
        xy_distances.append((distance_x, distance_y))
    return xy_distances


AIT_COLORS = {'bordeaux':'#79151d', # 2
              'grau':'#7c8388', # 1
              'türkis':'#31b7bc', # 3
              'violet':'#470f51', # 4
              '50grau':'lightgray', 
              'schwarz':'#000c20'}

many_colors = ['xkcd:dark blue', 'xkcd:maroon'      , 'xkcd:orange'       , 'xkcd:aqua'        ,
               'xkcd:cyan'     , 'xkcd:sky blue'    , 'xkcd:lime'         , 'xkcd:hot pink'    ,
               'xkcd:slate'    , 'xkcd:spring green', 'xkcd:light red'    , 'xkcd:light violet',
               'xkcd:cream'    , 'xkcd:apple green' , 'xkcd:dark lavender', 'xkcd:terra cotta' ]

more_colors = ['xkcd:blue green', 'xkcd:cerulean', 'xkcd:coral', 'xkcd:steel',
               'xkcd:mauve'     , 'xkcd:orange'  , 'xkcd:pink' , 'xkcd:peach',
               'xkcd:indigo'    , 'xkcd:lime'    , 'xkcd:gold' , 'xkcd:slate',
               'xkcd:greenish'  , 'xkcd:grape'   , 'xkcd:sky'  , 'xkcd:clay' ,
               'xkcd:azure'     , 'xkcd:lemon'   , 'xkcd:shit' , 'xkcd:melon',
               'xkcd:ecru'      , 'xkcd:silver'  , 'xkcd:ocre' , 'xkcd:neon red' ]
