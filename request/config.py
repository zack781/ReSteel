import ezdxf
import numpy as np
import cv2
from shapely.geometry import Polygon
from shapely.geometry import MultiPolygon
from shapely.ops import unary_union
import ezdxf
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, MultiPoint
import ezdxf
import numpy as np
from shapely.geometry import Polygon, MultiPoint
from shapely.affinity import rotate
MASK_SCALE = 2.0                 
STEP_SIZE_MM = 1.0              
ROTATION_ANGLES = range(0, 180, 15) 
VERBOSE = True                   
