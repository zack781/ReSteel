import ezdxf
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, MultiPolygon
from shapely.affinity import translate, rotate
from shapely.ops import unary_union
import random

def extract_polygon_from_dxf(dxf_path):
    """Extract closed polygon from DXF."""
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    points = []
    for entity in msp:
        if entity.dxftype() in ['LWPOLYLINE', 'POLYLINE']:
            for p in entity.get_points():
                points.append((p[0], p[1]))
    if not points:
        raise ValueError("No valid shape found in DXF")
    if points[0] != points[-1]:  # ensure closed
        points.append(points[0])
    return Polygon(points)

def blf_place_polygons(base_poly, n_copies, spacing=5, rotation_angles=[0, 90, 180, 270]):
    """Bottom-Left-Fill placement with rotation."""
    placed_polys = []
    insert_points = [(0, 0)]  # Start from origin
    base_polys = [base_poly for _ in range(n_copies)]
    canvas = []  # already placed polygons

    for idx, poly in enumerate(base_polys):
        best_candidate = None
        best_point = None
        best_angle = None
        best_metric = None

        # Try every insert point + rotation
        for point in insert_points:
            for angle in rotation_angles:
                rotated = rotate(poly, angle, origin='centroid', use_radians=False)
                minx, miny, _, _ = rotated.bounds
                translated = translate(rotated, xoff=point[0] - minx, yoff=point[1] - miny)

                # Check collision
                collision = False
                for existing in canvas:
                    if translated.intersects(existing):
                        collision = True
                        break

                if not collision:
                    # Calculate bounding box area after placing
                    trial_canvas = canvas + [translated]
                    union_bounds = unary_union(trial_canvas).bounds
                    width = union_bounds[2] - union_bounds[0]
                    height = union_bounds[3] - union_bounds[1]
                    area = width * height
                    aspect_ratio = max(width / height, height / width)
                    metric = area * (1 + 0.2 * (aspect_ratio - 1))  # prioritize small area and balanced shape

                    if (best_metric is None) or (metric < best_metric):
                        best_candidate = translated
                        best_point = point
                        best_angle = angle
                        best_metric = metric

        if best_candidate is None:
            raise RuntimeError(f"Cannot place shape #{idx}")

        # Place the best found candidate
        placed_polys.append(best_candidate)
        canvas.append(best_candidate)

        # Update insert points
        for x, y in best_candidate.exterior.coords:
            insert_points.append((x, y))

        # Optional: remove duplicate points
        insert_points = list(set(insert_points))

    return placed_polys

def save_combined_dxf(polygons, output_path):
    """Save list of polygons to a DXF file."""
    doc = ezdxf.new()
    msp = doc.modelspace()
    for poly in polygons:
        coords = list(poly.exterior.coords)
        msp.add_lwpolyline(coords, close=True)
    doc.saveas(output_path)
    print(f"Saved combined DXF: {output_path}")

def plot_polygons(polygons, title="Polygon Nesting Result"):
    """Plot polygons."""
    plt.figure(figsize=(8,8))
    for poly in polygons:
        x, y = poly.exterior.xy
        plt.plot(x, y, 'b--')
        plt.fill(x, y, alpha=0.3)
    plt.axis('equal')
    plt.grid(True)
    plt.title(title)
    plt.show()

def nest(request_dxf, n_copies, output_dxf, spacing=1, rotation_angles=[0 ,30,60,90,120,150, 180, 210,240,270,300,330]):
    """Full Nesting Pipeline."""
    base_poly = extract_polygon_from_dxf(request_dxf)
    placed_polys = blf_place_polygons(
        base_poly, 
        n_copies=n_copies,
        spacing=spacing,
        rotation_angles=rotation_angles
    )

    minx, miny, maxx, maxy = unary_union(placed_polys).bounds
    total_area = (maxx - minx) * (maxy - miny)
    width = maxx - minx
    height = maxy - miny

    print(f"Final Total Area = {total_area:.2f} (Width={width:.2f}, Height={height:.2f})")

    save_combined_dxf(placed_polys, output_dxf)
    plot_polygons(placed_polys, title=f"Nesting Result (Area={total_area:.1f})")

    return total_area, width, height
