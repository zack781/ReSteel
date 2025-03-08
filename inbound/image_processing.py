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
    print(f"✅ DXF file saved to: {dxf_output_path}")
