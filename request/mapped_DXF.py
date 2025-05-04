from request.config import MASK_SCALE, STEP_SIZE_MM
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
    print(f"Final DXF saved: {output_dxf_path}")

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

# def largestRectangleArea(heights):
#     if not heights:
#         return 0, 0, 0, 0
#     heights = list(heights) + [0]
#     stack = []
#     max_area, left, right, max_h = 0, 0, 0, 0
#     for i, h in enumerate(heights):
#         while stack and h < heights[stack[-1]]:
#             print(f"[DEBUG] i={i}, h={h}, stack={stack}, heights={heights}")
#             top_idx = stack.pop()
#             height = heights[top_idx]
#             l = stack[-1] + 1 if stack else 0
#             area = height * (i - l)
#             print(f"[DEBUG] pop index={top_idx}, height={height}, l={l}, area={area}")
#         stack.append(i)
#     return max_area, left, right, max_h
def largestRectangleArea(heights):
    if not heights:
        return 0, 0, 0, 0  # area, l_val, r_val, max_h
    heights = list(heights) + [0]  # 加哨兵
    stack = []
    max_area, left, right, max_h = 0, 0, 0, 0
    for i, h in enumerate(heights):
        if stack and h < heights[stack[-1]]:
            # 第一次发现下降，pop一次
            height = heights[stack.pop()]
            l = stack[-1] + 1 if stack else 0
            area = height * (i - l)
            if area > max_area:
                max_area = area
                left, right = l, i - 1
                max_h = height  
            stack.append(i)
            break  
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

def find_best_placement(request_shape, rec, step=100.0, scale=MASK_SCALE):
    """Search for the best placement that maximizes remaining usable rectangular area."""
    x0, y0, w, h = rec
    rec_poly = Polygon([(x0, y0), (x0+w, y0), (x0+w, y0+h), (x0, y0+h)])
    request_poly = Polygon(request_shape)
    if not request_poly.is_valid:
        request_poly = request_poly.buffer(0)

    minx, miny, maxx, maxy = request_poly.bounds
    req_w = maxx - minx
    req_h = maxy - miny

    dx_range = np.arange(x0, x0 + w - req_w + 0.5, step)
    dy_range = np.arange(y0, y0 + h - req_h + 0.5, step)

    best_score = -1
    best_transformed = None

    for dx in dx_range:
        for dy in dy_range:
            translated = [(x - minx + dx, y - miny + dy) for x, y in request_shape]
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



import ezdxf
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
from shapely.affinity import scale, translate
import matplotlib.pyplot as plt
def load_all_shapes_from_dxf(dxf_path):
    """Load all closed LWPOLYLINE shapes from a DXF file."""
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    shapes = []

    for entity in msp.query("LWPOLYLINE"):
        if entity.dxf.flags & 1:  # closed
            points = [p[0:2] for p in entity.get_points()]
            shapes.append(Polygon(points))
    
    if not shapes:
        raise ValueError("No closed shapes found in DXF.")
    
    return shapes

def embed_nesting_to_rec(nested_dxf_path, material_dxf_path, rec, output_dxf_path):
    """Embed a nesting layout into a given rectangle (rec) on a material (Rotation + Translation, No scaling)."""
    # 1. Load all polygons
    shapes = load_all_shapes_from_dxf(nested_dxf_path)

    # 2. Extract rec
    rec_x, rec_y, rec_w, rec_h = rec
    need_angle= np.linspace(0,360,10)
    for angle in need_angle:
        # Rotate all shapes around center
        combined = unary_union(shapes)
        center_x, center_y = combined.centroid.xy
        center_x, center_y = center_x[0], center_y[0]

        rotated_shapes = []
        for poly in shapes:
            rotated = rotate(poly, angle=angle, origin=(center_x, center_y), use_radians=False)
            rotated_shapes.append(rotated)

        # Check bounding box
        rotated_combined = unary_union(rotated_shapes)
        minx, miny, maxx, maxy = rotated_combined.bounds
        width = maxx - minx
        height = maxy - miny

        if width <= rec_w and height <= rec_h:
            # Good, can fit
            delta_x = rec_x - minx
            delta_y = rec_y - miny

            final_shapes = []
            for poly in rotated_shapes:
                moved = translate(poly, xoff=delta_x, yoff=delta_y)
                final_shapes.append(moved)

            # Save into material
            material_doc = ezdxf.readfile(material_dxf_path)
            msp = material_doc.modelspace()

            for poly in final_shapes:
                coords = list(poly.exterior.coords)
                msp.add_lwpolyline(coords, close=True)

            material_doc.saveas(output_dxf_path)
            print(f"[✓] Final rotated {angle}°, placed DXF saved: {output_dxf_path}")

            # Optional: Plot
            plt.figure(figsize=(8,8))
            for poly in final_shapes:
                x, y = poly.exterior.xy
                plt.plot(x, y, 'b--')
                plt.fill(x, y, alpha=0.3)
            plt.axis('equal')
            plt.title(f"Nesting embedded with rotation {angle}°")
            plt.grid(True)
            plt.show()

            return  # Success!

    # If all angles failed
    raise RuntimeError("Cannot fit the nesting into the given rec with any 0/90/180/270° rotation.")
