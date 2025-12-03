# FortilineFL-GEO-COUNTY-OVRLY
Interactive map that overlays Floridas Fortiline Waterworks Locations with counties.

Using ChatGPT I created the following prompt to then use withing cursor.

ChatGPT prompt: Help me write a prompt in cursor that will make a data visualization using Python to overlay
all counties in Florida (should be able to zoom in and out)
with all locations of Fortiline Waterworks (my employer). Pulling these addresses from the internet.

This then created the following prompt which was used within Cursor:

You are an expert Python GIS and data visualization engineer.

**Goal**

Create a complete, runnable Python script that:

1. Builds an interactive, zoomable map of **all counties in Florida**.
2. Overlays **all Fortiline Waterworks branches located in Florida** as point markers.
3. Lets me pan/zoom and click each Fortiline marker to see its branch name and address.
4. Saves the output as an HTML file (e.g. `fortiline_florida_map.html`) that I can open in a browser.

---

### Tech & Libraries

Use ONLY standard Python + common geo/data libraries that I can install with pip:

- `requests` (for HTTP)
- `pandas`
- `geopandas`
- `folium`
- `geopy` (Nominatim geocoder or similar) for converting addresses to lat/long

At the top of the script, include a comment with the pip install line, e.g.:

```python

#pip install requests pandas geopandas folium geopy
```



-Output and fnal product in other files

To Run

1)install depencies
```
pip install requests pandas geopandas folium geopy
```
2)Run the Script
```
python overlay.py




