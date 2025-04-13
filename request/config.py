import os
import cv2
import numpy as np
import sqlite3
import ezdxf
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, MultiPolygon, MultiPoint
from shapely.ops import unary_union
from shapely.affinity import rotate
from rectpack import newPacker

MASK_SCALE = 2.0                 
STEP_SIZE_MM = 1.0              
ROTATION_ANGLES = range(0, 180, 15) 
VERBOSE = True                   
