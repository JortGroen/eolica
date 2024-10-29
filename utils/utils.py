import math
from geopy import distance
import numpy as np

def get_xy_from_gps(lat, long): ## this has to be in degrees N/S and degrees E/W
    '''
    helper function that translates from gps coordinates to xy coordinates

    :param lat: latitude of the point
    :param long: longitude of the point
    '''

    y = distance.distance( (lat, 0.) , (0. ,0.) ).meters
    x = distance.distance( (0., long) , (0. ,0.) ).meters
    return (x, y)

AIT_COLORS = {'bordeaux':'#79151d', # 2
              'grau':'#7c8388', # 1
              'türkis':'#31b7bc', # 3
              'violet':'#470f51', # 4
              '50grau':'lightgray', 
              'schwarz':'#000c20'}

colors = ['xkcd:dark blue', 'xkcd:maroon'      , 'xkcd:orange'       , 'xkcd:aqua'        ,
          'xkcd:cyan'     , 'xkcd:sky blue'    , 'xkcd:lime'         , 'xkcd:hot pink'    ,
          'xkcd:slate'    , 'xkcd:spring green', 'xkcd:light red'    , 'xkcd:light violet',
          'xkcd:cream'    , 'xkcd:apple green' , 'xkcd:dark lavender', 'xkcd:terra cotta' ]

#colors = ['xkcd:blue green', 'xkcd:cerulean', 'xkcd:coral', 'xkcd:steel',
#          'xkcd:mauve'     , 'xkcd:orange'  , 'xkcd:pink' , 'xkcd:peach',
#          'xkcd:indigo'    , 'xkcd:lime'    , 'xkcd:gold' , 'xkcd:slate',
#          'xkcd:greenish'  , 'xkcd:grape'   , 'xkcd:sky'  , 'xkcd:clay' ,
#          'xkcd:azure'     , 'xkcd:lemon'   , 'xkcd:shit' , 'xkcd:melon',
#          'xkcd:ecru'      , 'xkcd:silver'  , 'xkcd:ocre' , 'xkcd:neon red' ]
