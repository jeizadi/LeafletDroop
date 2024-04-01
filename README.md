# LeafletDroop
The leaflet droop measurement program accepts all .JPEG files and allows for user identification of scale and horizontal coordinate system of interest to generate output files from a single selected point measuring the distance perpendicular to the horizontal coordinate system to the point of interest and appends the distance value to an excel output file for ease of batch sorting.

## Input File Format
.JPEG files accepted - must contain a scale for calibration purposes

# How to Use for Leaflet Droop Measurement
## Initialize Calibration 
Follow prompts to enter the known distance (in millimeters) and select points along the known length to best approximate the line segment used for scale

Select the Accept Calibration button when satisfied with the approximation
## Re-Calibration
Once a calibration scale is initialized, the scale can be re-initialized by selecting the "Re-Calibration" button

## Initialize Horizontal Coordinate System 
Follow prompts to select a line segment along the elected horizontal coordinate system 

Select the Accept Horizontal button when satisfied with the approximation
## Re-Draw Horizontal
Once a horizontal coordinate line has been selected, this system can be modified by selecting the "Re-Draw Horizontal" button

## Measure Leaflet Droop Value
After both the calibration and horizontal coordinate system have been initialized, follow the prompt to select a single point for leaflet droop measurement calculation. This distance will be drawn perpendicular to the line approximating the horizontal coordinate system. 

Once satisfied with the point selection, select the "Accept and Save" button to save the output image and write the distance value and leaflet lot identifiers to the (existing) output Excel file in the file location of the original input image. 

# Outputs
1. Output image (.PNG) named according to the input image, current date & time, and marked with a "_M" and contains the original image with the calibration scale (green), horizontal coordinate system (green), distance measurements (blue), and point (red) along with an identifier and output in the upper left corner
2. Excel file appended with the leaflet lot identifiers and droop length: "Leaflet Assembly Lot #", "Leaflet", "Droop Length (mm)"

# Notes
The calibration scale and horizontal coordinate system will carry over when opening a new image file to facilitate ease of measurement given the fixed set-up. These can be overridden by selecting either the "Re-Calibration" or "Re-Draw Horizontal" buttons at any time. 

Zoom Functionality: Hold the left Control Key down (Ctrl-L) and scroll up on a mouse wheel to zoom into the region located at the mouse position on the image -OR- hold the left Control Key down (Ctrl-L) and scroll down on a mouse wheel to zoom out. 
