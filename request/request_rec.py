import numpy as np
import cv2
import ezdxf
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, MultiPolygon, MultiPoint
from shapely.ops import unary_union
from shapely.affinity import rotate

from config import MASK_SCALE, STEP_SIZE_MM, ROTATION_ANGLES, VERBOSE

def extract_points_from_dxf(filename):
    doc = ezdxf.readfile(filename)
    msp = doc.modelspace()
    points = []

    for entity in msp:
        if entity.dxftype() in ['LINE', 'LWPOLYLINE', 'POLYLINE']:
            if entity.dxftype() == 'LINE':
                points.append((entity.dxf.start.x, entity.dxf.start.y))
                points.append((entity.dxf.end.x, entity.dxf.end.y))
            else:
                for point in entity.get_points():
                    points.append((point[0], point[1]))
    return points

def compute_min_bounding_rect(points):
    multipoint = MultiPoint(points)
    min_rect = multipoint.minimum_rotated_rectangle
    rect_coords = list(min_rect.exterior.coords)
    return rect_coords[:-1]  # remove closing point

def analyze_dxf_outline(dxf_path):
    """
    Load a DXF file, compute its minimum bounding rectangle (MBR),
    and visualize the original shape.
    
    Returns:
        width (float), height (float)
    """
    # Extract points
    points = extract_points_from_dxf(dxf_path)
    if not points:
        raise ValueError("No shape found in the DXF file.")

    # Compute MBR
    mbr = compute_min_bounding_rect(points)
    mbr_poly = Polygon(mbr)
    minx, miny, maxx, maxy = mbr_poly.bounds
    width = maxx - minx
    height = maxy - miny

    # Plot
    points_np = np.array(points)
    if not np.array_equal(points_np[0], points_np[-1]):
        points_np = np.vstack([points_np, points_np[0]])  # close loop

    plt.figure(figsize=(6, 6))
    plt.plot(points_np[:, 0], points_np[:, 1], 'b--', linewidth=1.5, label='Original Shape')
    plt.plot(mbr_np[:, 0], mbr_np[:, 1], 'r-', linewidth=2.0, label='rec')
    plt.scatter(points_np[:, 0], points_np[:, 1], color='gray', s=30)
    plt.axis('equal')
    plt.grid(True)
    plt.legend()
    plt.title('Shape and Minimum Bounding Rectangle')
    plt.show()

    return width, height
