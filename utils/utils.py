import math
from geopy import distance
import numpy as np

def get_xy_from_gps(lat, long): ## this has to be in degrees N/S and degrees E/W

    y = distance.distance( (lat, 0.) , (0. ,0.) ).meters

    x = distance.distance( (0., long) , (0. ,0.) ).meters


    return (x, y)

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
