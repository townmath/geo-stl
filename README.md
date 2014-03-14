geo-stl
=======

Program to take a file from GeoMapApp and turn it into an 3-D printable *.stl file

Directions: 
 1. Open GeoMapApp http://www.geomapapp.org/
 2. Zoom into the location you want to print
 3. Show the Grid Dialogue
 4. Under Palettes Menu select Black to White and Normalize
 5. Turn off the Sun
 6. File->Preferences Uncheck the Map Annotations Boxes
 7. File->Save Map Window as Image/Grid File
 8. Save as a .png
 9. Before you close GeoMapApp, write down the highest and lowest elevation
 10. Open geo-stl
 11. Set high point and low point
 12. Set Vertical Exaggeration (1 looks good, but .5 is closest to real life)
 13. Select File
 14. Start (takes a while)
 15. Your file will be saved in the same directory as the image you chose. 
 16. Print and enjoy!


Dependencies:
 - scipy
 - stl_tools
 - Image
 - Tkinter
 - numpy
 - tkFileDialog
 - sys
