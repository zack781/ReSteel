from request.config import MASK_SCALE, STEP_SIZE_MM, ROTATION_ANGLES, VERBOSE
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
def load_request_shape(request_dxf_path):
    """Load a closed LWPOLYLINE shape from request.dxf."""
    doc = ezdxf.readfile(request_dxf_path)
    msp = doc.modelspace()
    for entity in msp.query("LWPOLYLINE"):
        if entity.dxf.flags & 1:  # closed
            points = [p[0:2] for p in entity.get_points()]
            return points
    raise ValueError("No closed LWPOLYLINE found in request DXF.")

def insert_shape_to_material(material_dxf_path, output_dxf_path, shape_coords):
    """Insert the given shape into the material DXF and save the result."""
    doc = ezdxf.readfile(material_dxf_path)
    msp = doc.modelspace()
    msp.add_lwpolyline(shape_coords, close=True)
    doc.saveas(output_dxf_path)
    print(f"[✓] Final DXF saved: {output_dxf_path}")

def polygon_to_mask(polygon: Polygon, bounds, scale: float) -> np.ndarray:
    """Convert a shapely Polygon into a binary mask (0/1)."""
    x_min, y_min, x_max, y_max = bounds
    w = int(np.ceil((x_max - x_min) * scale))
    h = int(np.ceil((y_max - y_min) * scale))
    mask = np.zeros((h, w), dtype=np.uint8)

    if polygon.is_empty:
        return mask

    if polygon.geom_type == "Polygon":
        polygons = [polygon]
    elif polygon.geom_type == "MultiPolygon":
        polygons = list(polygon.geoms)
    else:
        return mask

    for poly in polygons:
        pts = np.array([
            [(x - x_min) * scale, (y - y_min) * scale]
            for x, y in poly.exterior.coords
        ], dtype=np.int32)
        cv2.fillPoly(mask, [pts], 1)

    return mask

def largestRectangleArea(heights):
    stack = []
    max_area, left, right, max_h = 0, 0, 0, 0
    for i, h in enumerate(list(heights) + [0]):
        while stack and h < heights[stack[-1]]:
            height = heights[stack.pop()]
            l = stack[-1] + 1 if stack else 0
            area = height * (i - l)
            if area > max_area:
                max_area = area
                left, right, max_h = l, i - 1, height
        stack.append(i)
    return max_area, left, right, max_h

def maximalRectangle(matrix):
    if matrix.size == 0:
        return 0, None
    h, w = matrix.shape
    heights = [0] * w
    max_area, max_rect = 0, None
    for i in range(h):
        for j in range(w):
            heights[j] = heights[j] + 1 if matrix[i, j] == 1 else 0
        area, l, r, h_val = largestRectangleArea(heights)
        if area > max_area:
            max_area = area
            max_rect = (i - h_val + 1, l, i, r)
    return max_area, max_rect

def find_best_placement(request_shape, rec, step=STEP_SIZE_MM, scale=MASK_SCALE, rotate_range=ROTATION_ANGLES):
    """Search for the best placement (including rotation) that maximizes remaining usable area."""
    x0, y0, w, h = rec
    rec_poly = Polygon([(x0, y0), (x0+w, y0), (x0+w, y0+h), (x0, y0+h)])
    original_poly = Polygon(request_shape)
    if not original_poly.is_valid:
        original_poly = original_poly.buffer(0)

    best_score = -1
    best_transformed = None

    for angle in rotate_range:
        rotated_poly = rotate(original_poly, angle, origin='center', use_radians=False)
        minx, miny, maxx, maxy = rotated_poly.bounds
        req_w = maxx - minx
        req_h = maxy - miny

        dx_range = np.arange(x0, x0 + w - req_w + 0.5, step)
        dy_range = np.arange(y0, y0 + h - req_h + 0.5, step)

        for dx in dx_range:
            for dy in dy_range:
                translated = [(x - minx + dx, y - miny + dy) for x, y in rotated_poly.exterior.coords[:-1]]
                translated_poly = Polygon(translated)
                if not translated_poly.is_valid or not rec_poly.contains(translated_poly):
                    continue

                remaining = rec_poly.difference(translated_poly)
                bounds = remaining.bounds
                mask = polygon_to_mask(remaining, bounds, scale)
                area, rect = maximalRectangle(mask)
                if rect and area > best_score:
                    best_score = area
                    best_transformed = translated

    if best_transformed is None:
        raise RuntimeError("Request shape cannot be placed inside the given rectangle.")
    return best_transformed

def embed_request_to_rec(request_dxf, material_dxf, rec, output_dxf, optimize=True, step=STEP_SIZE_MM):
    """Main entry: embed request shape into material DXF based on rec rectangle."""
    shape = load_request_shape(request_dxf)
    if optimize:
        shape = find_best_placement(shape, rec, step=step)
    insert_shape_to_material(material_dxf, output_dxf, shape)
