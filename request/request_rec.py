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

def request_rec_output(dxf_path):
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
    mbr_np = np.array(mbr)

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


def request_rec_output_nesting(dxf_path, n_copies=3, save_combined_dxf_path=None, padding=0):
    """
    Load a DXF file, replicate n copies with auto compact nesting, and output combined shape and size.
    
    Args:
        dxf_path (str): path to the input dxf file
        n_copies (int): number of copies to nest
        save_combined_dxf_path (str): if given, save the combined DXF here
        padding (float): padding between parts

    Returns:
        combined_width (float), combined_height (float), combined_shape (list of (x, y))
    """
    # Step 1. Extract points
    points = extract_points_from_dxf(dxf_path)
    if not points:
        raise ValueError("No shape found in the DXF file.")

    # Step 2. Compute single shape bounding box
    mbr = compute_min_bounding_rect(points)
    mbr_poly = Polygon(mbr)
    minx, miny, maxx, maxy = mbr_poly.bounds
    single_width = maxx - minx
    single_height = maxy - miny

    # Step 3. Set up rectpack packer
    packer = newPacker(rotation=False)  # rotation=False表示不旋转放置

    for _ in range(n_copies):
        packer.add_rect(single_width + padding, single_height + padding, rid=_)

    # 大箱子尺寸一开始可以估计大一点
    bin_width = (single_width + padding) * n_copies
    bin_height = (single_height + padding) * n_copies
    packer.add_bin(bin_width, bin_height)

    packer.pack()

    # Step 4. Get the placement result
    combined_shape = []
    max_right = 0
    max_top = 0

    for rect in packer.rect_list():
        print(rect)
        bin_idx, x, y, w, h, rid = rect

        # Translate original points
        translated = [(p[0] - minx + x, p[1] - miny + y) for p in points]
        combined_shape.extend(translated)
        max_right = max(max_right, x + w)
        max_top = max(max_top, y + h)

    combined_width = max_right
    combined_height = max_top

    # Step 5. Save combined DXF
    if save_combined_dxf_path:
        doc = ezdxf.new()
        msp = doc.modelspace()
        msp.add_lwpolyline(combined_shape, close=True)
        doc.saveas(save_combined_dxf_path)
        print(f"Combined DXF saved: {save_combined_dxf_path}")

    # Step 6. Plot
    points_np = np.array(combined_shape)
    if not np.array_equal(points_np[0], points_np[-1]):
        points_np = np.vstack([points_np, points_np[0]])
    plt.figure(figsize=(8, 6))
    plt.plot(points_np[:, 0], points_np[:, 1], 'b--', linewidth=1.5, label='Combined Shape (Auto Nesting)')
    plt.scatter(points_np[:, 0], points_np[:, 1], color='gray', s=30)
    plt.axis('equal')
    plt.grid(True)
    plt.legend()
    plt.title(f'Auto Nested Shape ({n_copies} copies)')
    plt.show()

    return combined_width, combined_height
