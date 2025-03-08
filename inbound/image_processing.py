def process_image_to_dxf(image_path, dxf_output_path, p1_hsv_range=None, p2_hsv_range=None):
    """ Process image -> Contour detection -> DXF generation (retain external and internal contours, remove noise & P1P2 markers) """

    # Read the original image
    image = cv2.imread(image_path)

    # Convert to HSV color space
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Set HSV color range for P1 (red)
    if p1_hsv_range is None:
        p1_hsv_range = [(np.array([0, 100, 100]), np.array([10, 255, 255])),
                        (np.array([170, 100, 100]), np.array([180, 255, 255]))]
    
    mask_red = sum(cv2.inRange(hsv, lower, upper) for lower, upper in p1_hsv_range)
    
    # Set HSV color range for P2 (green)
    if p2_hsv_range is None:
        p2_hsv_range = [(np.array([35, 80, 80]), np.array([85, 255, 255]))]
    
    mask_green = sum(cv2.inRange(hsv, lower, upper) for lower, upper in p2_hsv_range)
    
    # Generate P1P2 color mask
    mask = mask_red + mask_green

    # Morphological operation - Expand mask (remove marker points)
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=2)  # Expand mask area appropriately

    # Directly fill white to remove markers
    image[mask > 0] = [255, 255, 255]

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Binarization (post-processing after removing P1P2)
    _, thresh = cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY)

    # Display binarized image (for inspection)
    plt.figure(figsize=(5,5))
    plt.imshow(thresh, cmap='gray')
    plt.title("Thresholded Image (Wood Shape)")
    plt.axis("off")
    plt.show()

    # Contour detection (detect all levels, including external and internal contours)
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Find the largest external contour (wood board body)
    max_area = 0
    main_contour_index = -1
    for i, cnt in enumerate(contours):
        area = cv2.contourArea(cnt)
        if area > max_area:
            max_area = area
            main_contour_index = i  # Record the largest contour index (wood board)

    # Generate DXF file
    doc = ezdxf.new()
    msp = doc.modelspace()
    shape_contours = []

    # Process all contours
    for i, cnt in enumerate(contours):
        epsilon = 0.005 * cv2.arcLength(cnt, True)  # Adjust to 0.01 to reduce corner points
        approx = cv2.approxPolyDP(cnt, epsilon, True)

        if len(approx) >= 4 and cv2.contourArea(cnt) > 800:  # Adjust filter area to 800
            poly = Polygon([tuple(p[0]) for p in approx])

            if i == main_contour_index:  # This is the largest external contour (wood board body)
                shape_contours.append(poly)
                msp.add_lwpolyline(list(poly.exterior.coords), close=True)
            elif hierarchy[0][i][3] == main_contour_index:  # This is a hole inside the wood board
                shape_contours.append(poly)
                msp.add_lwpolyline(list(poly.exterior.coords), close=True)

    # Save DXF
    doc.saveas(dxf_output_path)
    print(f"DXF file saved to: {dxf_output_path}")


def largestRectangleArea(heights):
    """ Calculate the maximum rectangular area (histogram algorithm). """
    stack = []
    max_area, left_index, right_index, max_h = 0, 0, 0, 0
    for i, h in enumerate(list(heights) + [0]):
        while stack and h < heights[stack[-1]]:
            cur_h = heights[stack.pop()]
            cur_left = stack[-1] + 1 if stack else 0
            cur_width = i - cur_left
            area = cur_h * cur_width
            if area > max_area:
                max_area, left_index, right_index, max_h = area, cur_left, i - 1, cur_h
        stack.append(i)
    return max_area, left_index, right_index, max_h


def maximalRectangle(matrix):
    """ Compute the maximum usable rectangle (axis-aligned). """
    if matrix.size == 0:
        return 0, None
    n_rows, n_cols = matrix.shape
    heights = [0] * n_cols
    max_area, max_rect = 0, None
    for i in range(n_rows):
        for j in range(n_cols):
            heights[j] = heights[j] + 1 if matrix[i, j] == 1 else 0
        area, left, right, h_val = largestRectangleArea(heights)
        if area > max_area:
            max_area = area
            row_bottom = i
            row_top = i - h_val + 1
            max_rect = (row_top, left, row_bottom, right)
    return max_area, max_rect


def load_scaled_dxf_and_find_max_rectangles(dxf_input_path, dxf_output_path, scale):
    """ Reads a scaled DXF file and extracts the largest available rectangles (MIRs). """
    doc = ezdxf.readfile(dxf_input_path)
    msp = doc.modelspace()

    contours = []
    for entity in msp.query("LWPOLYLINE"):
        points = [(p[0], p[1]) for p in entity.get_points()]
        poly = Polygon(points)
        if poly.is_valid and poly.area > 50:
            contours.append(poly)

    if not contours:
        print("No valid contours found!")
        return

    contours.sort(key=lambda p: p.area, reverse=True)
    board_poly = contours[0]
    hole_polys = contours[1:]

    x_min, y_min, x_max, y_max = board_poly.bounds
    board_width = int(np.ceil((x_max - x_min) * scale))
    board_height = int(np.ceil((y_max - y_min) * scale))
    available_mask = np.zeros((board_height, board_width), dtype=np.uint8)

    board_points = np.array([[int((p[0] - x_min) * scale), int((p[1] - y_min) * scale)] for p in board_poly.exterior.coords], dtype=np.int32)
    cv2.fillPoly(available_mask, [board_points], 255)

    for hole in hole_polys:
        hole_points = np.array([[int((p[0] - x_min) * scale), int((p[1] - y_min) * scale)] for p in hole.exterior.coords], dtype=np.int32)
        cv2.fillPoly(available_mask, [hole_points], 0)

    binary_mask = (available_mask == 255).astype(np.uint8)
    rectangles = []

    while True:
        area, rect = maximalRectangle(binary_mask)
        if rect is None:
            break

        y1, x1, y2, x2 = rect
        width = x2 - x1 + 1
        height = y2 - y1 + 1
        
        area_mm = area / (scale ** 2)
        width_mm = width / scale
        height_mm = height / scale
        if area_mm < MIN_USABLE_AREA_MM or width_mm < MIN_RECT_SIZE_MM or height_mm < MIN_RECT_SIZE_MM:
            break

        x_real = x1 / scale + x_min
        y_real = y1 / scale + y_min
        
        rectangles.append((x_real, y_real, width_mm, height_mm))
        binary_mask[y1:y2+1, x1:x2+1] = 0

    if not rectangles:
        print("No suitable available rectangles found")
        return

    for x, y, w, h in rectangles:
        rect_coords = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
        msp.add_lwpolyline(rect_coords, close=True)

    doc.saveas(dxf_output_path)
    print(f"DXF processing completed, saved to: {dxf_output_path}")
    print(f"Found {len(rectangles)} rectangles")
    return rectangles


def compute_scale(P1_pixel, P2_pixel, dxf_input_path, dxf_output_path):
    """ Compute the scaling factor, rotate P1P2 to make it horizontal, and output the scaled DXF """

    # Compute the distance of P1P2 in pixel space
    d_pixel = np.linalg.norm(np.array(P2_pixel) - np.array(P1_pixel))

    # Compute the scaling factor from pixels to millimeters
    scale = REAL_P1P2_DISTANCE_MM / d_pixel

    # Compute the angle of P1P2 relative to the x-axis
    theta = np.arctan2(P2_pixel[1] - P1_pixel[1], P2_pixel[0] - P1_pixel[0])

    # Compute the rotation matrix (counterclockwise rotation by -theta)
    cos_theta = np.cos(-theta)
    sin_theta = np.sin(-theta)

    # Read DXF
    doc = ezdxf.readfile(dxf_input_path)
    msp = doc.modelspace()

    # Transform DXF coordinates: set P1 as (0,0), then scale & rotate
    for entity in msp.query("LWPOLYLINE"):
        new_points = []
        for p in entity.get_points():
            # Translate to make P1 the new (0,0)
            x, y = p[0] - P1_pixel[0], p[1] - P1_pixel[1]

            # Rotate to make P2 become (10,0)
            x_new = cos_theta * x - sin_theta * y
            y_new = sin_theta * x + cos_theta * y

            # Scale
            new_points.append((x_new * scale, y_new * scale))

        entity.set_points(new_points)

    # Compute the positions of P1 and P2 in millimeter coordinates
    P1_real = (0, 0)  # Set P1 as DXF (0,0)
    P2_real = (10, 0)  # After rotation, P2 is fixed at (10,0)

    # Annotate P1 and P2 in the DXF
    msp.add_circle(P1_real, 1)
    msp.add_circle(P2_real, 1)
    msp.add_text("P1", dxfattribs={"insert": (P1_real[0] + 2, P1_real[1] + 2), "height": 2})
    msp.add_text("P2", dxfattribs={"insert": (P2_real[0] + 2, P2_real[1] + 2), "height": 2})

    #**Correct dimension annotation between P1 and P2**
    dim = msp.add_linear_dim(
        base=((P1_real[0] + P2_real[0]) / 2, P1_real[1] - 5),  # Dimension line placed below P1P2
        p1=P1_real,  # P1 coordinates
        p2=P2_real,  # P2 coordinates
        angle=0,  # Horizontal direction
        dxfattribs={"layer": "DIMENSIONS", "color": 2}
    )
    dim.render()

    # Save DXF
    doc.saveas(dxf_output_path)
    print(f"Scaled & Rotated DXF saved: {dxf_output_path}")
    return scale



def transform_dxf_with_p1_p2(dxf_input_path, dxf_output_path, scale):
    """ Read a DXF file, apply scaling and transformation based on P1P2, and annotate P1P2 """
    scale = float(scale)  # Ensure scale is a float
    # Read DXF
    doc = ezdxf.readfile(dxf_input_path)
    msp = doc.modelspace()

    # Filter out the P1P2 contour and keep only the material outline
    valid_entities = []
    for entity in msp.query("LWPOLYLINE"):
        points = entity.get_points()
        if len(points) > 4:  # Filter out P1P2 shapes (typically with fewer points)
            valid_entities.append(entity)

    # Clear the DXF and re-add only the valid contours
    doc.modelspace().delete_all_entities()
    for entity in valid_entities:
        points = [(p[0] - P1_pixel[0], p[1] - P1_pixel[1]) for p in entity.get_points()]
        scaled_points = [(x * scale, y * scale) for x, y in points]
        msp.add_lwpolyline(scaled_points, close=True)

    # Calculate P1P2 positions in millimeter coordinates
    P1_real = (0, 0)  # Set P1 as (0,0)
    P2_real = ((P2_pixel[0] - P1_pixel[0]) * scale, (P2_pixel[1] - P1_pixel[1]) * scale)

    # Keep only P1P2 text annotations without adding shapes
    msp.add_text("P1", dxfattribs={"insert": (P1_real[0] + 2, P1_real[1] + 2), "height": 5})
    msp.add_text("P2", dxfattribs={"insert": (P2_real[0] + 2, P2_real[1] + 2), "height": 5})

    # Save DXF
    doc.saveas(dxf_output_path)
    print(f"DXF transformation completed: {dxf_output_path} (P1P2 contour removed, only annotations retained)")


def detect_p1_p2(image_path, p1_hsv_range=None, p2_hsv_range=None):
    """ Detect P1 (red hollow circle) and P2 (green hollow circle), return pixel coordinates """
    
    # Read the image and convert it to the HSV color space
    image = cv2.imread(image_path)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # Set the HSV color range for P1 (red)
    if p1_hsv_range is None:
        p1_hsv_range = [(np.array([0, 100, 100]), np.array([10, 255, 255])),
                        (np.array([170, 100, 100]), np.array([180, 255, 255]))]
    
    mask_red = sum(cv2.inRange(hsv, lower, upper) for lower, upper in p1_hsv_range)
    contours_red, _ = cv2.findContours(mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    P1 = None
    for cnt in contours_red:
        (x, y), radius = cv2.minEnclosingCircle(cnt)
        if 3 < radius < 50:
            P1 = (int(x), int(y))
    
    # Set the HSV color range for P2 (green)
    if p2_hsv_range is None:
        p2_hsv_range = [(np.array([35, 80, 80]), np.array([85, 255, 255]))]
    
    mask_green = sum(cv2.inRange(hsv, lower, upper) for lower, upper in p2_hsv_range)
    contours_green, _ = cv2.findContours(mask_green, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    P2 = None
    for cnt in contours_green:
        (x, y), radius = cv2.minEnclosingCircle(cnt)
        if 3 < radius < 50:
            P2 = (int(x), int(y))
    
    if P1 is None or P2 is None:
        raise ValueError("Detection failed: Unable to correctly detect P1 (red O) or P2 (green O)")
    
    return P1, P2  # Return pixel coordinates


import os

def processing(image_path, dxf_intermediate_path, dxf_intermediate_scaled, dxf_output_path):
    """
    Process the input JPG file and generate the final DXF file.
    
    Parameters:
    image_path (str): Path to the input JPG file.
    dxf_intermediate_path (str): Path to the intermediate DXF file.
    dxf_intermediate_scaled (str): Path to the scaled intermediate DXF file.
    dxf_output_path (str): Path to the final DXF file.
    
    Returns:
    tuple: (Final DXF file path, calculated maximum usable rectangle rec((x_real, y_real, width_mm, height_mm)))
    """
    # 1. Identify contours and remove P1P2 markers
    process_image_to_dxf(image_path, dxf_intermediate_path)
    
    # 2. Detect P1 and P2
    P1_pixel, P2_pixel = detect_p1_p2(image_path)
    
    if P1_pixel and P2_pixel:
        # 3. Compute scaling factor
        scale = compute_scale(P1_pixel, P2_pixel, dxf_intermediate_path, dxf_intermediate_scaled)
        
        # 4. Apply DXF scaling
        
        # 5. Extract the largest usable rectangle and fill it
        rec = load_scaled_dxf_and_find_max_rectangles(dxf_intermediate_scaled, dxf_output_path, 1)
        print(rec)
        
        return dxf_output_path, rec
    else:
        print("Failed to detect P1 or P2. Please check the image quality.")
        return None, None
