import os
import cv2
import numpy as np
import sqlite3
import ezdxf
from shapely.geometry import Polygon
from rectpack import newPacker
import matplotlib.pyplot as plt

# Global constants
MIN_USABLE_AREA_MM = 900  # Minimum usable rectangular area (mm²)
MIN_RECT_SIZE_MM = 30  # Minimum side length (mm) to prevent extracting too small rectangles
REAL_P1P2_DISTANCE_MM = 100  # Real-world distance between P1 and P2 in mm
