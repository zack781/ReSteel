# README

## Overview
This script processes an input image to generate a DXF file while extracting the largest available rectangle. The processing involves contour detection, marker removal, DXF scaling, and geometric analysis.

## Usage
The main function to use is:
```python
processing(image_path, dxf_intermediate_path, dxf_intermediate_scaled, dxf_output_path)
```
### Parameters:
- `image_path` (str): Path to the input JPG image.
- `dxf_intermediate_path` (str): Path where the first DXF file (with detected contours) will be saved.
- `dxf_intermediate_scaled` (str): Path where the scaled DXF file will be saved after applying transformations.
- `dxf_output_path` (str): Path to the final processed DXF file containing the extracted largest usable rectangle.

### Returns:
- `dxf_output_path` (str): The path to the final DXF file.
- `rec` (tuple): The largest available rectangle in the format `(x_real, y_real, width_mm, height_mm)`, where:
  - `x_real, y_real` are the coordinates of the top-left corner in real-world units.
  - `width_mm, height_mm` represent the rectangle’s dimensions in millimeters.

## Example Usage
```python
final_dxf, largest_rectangle = processing(
    "input.jpg", 
    "intermediate.dxf", 
    "intermediate_scaled.dxf", 
    "final_output.dxf"
)
```
If successful, `final_dxf` will contain the path to the output DXF file, and `largest_rectangle` will contain the extracted rectangle’s properties.

## Dependencies
Ensure the following Python packages are installed before running the script:
```sh
pip install numpy opencv-python ezdxf shapely matplotlib
```

## Notes
- P1 and P2 are reference markers in the image (red and green circles) used to determine scale.
- The expected size of P1 and P2 circles should have a radius between **5 to 10 mm**.
- Given a reference distance of **100mm** between P1 and P2.
- If P1 or P2 detection fails, check the image quality and color representation.
- The script removes noise and retains only meaningful contours for DXF generation.


