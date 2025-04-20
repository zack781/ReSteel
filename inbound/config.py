import numpy as np
# Global constants
MIN_USABLE_AREA_MM = 900  # Minimum usable rectangular area (mm²)
MIN_RECT_SIZE_MM = 30  # Minimum side length (mm) to prevent extracting too small rectangles
REAL_P1P2_DISTANCE_MM = 100  # Real-world distance between P1 and P2 in mm
red_hsv = [
    (np.array([0, 80, 80]), np.array([10, 255, 255])),       # red (lower end)
    (np.array([160, 80, 80]), np.array([179, 255, 255]))     # red (upper end)
]
green_hsv_range = [
    (np.array([30, 40, 40]), np.array([95, 255, 255]))       # green/teal (expanded)
]
