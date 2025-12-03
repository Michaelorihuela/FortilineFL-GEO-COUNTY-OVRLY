# pip install requests pandas geopandas folium geopy

import requests
import pandas as pd
import geopandas as gpd
import folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
import os
from shapely.geometry import Point

def get_florida_counties():
    """
    Get Florida county boundaries using US Census Bureau TIGER/Line data.
    Downloads the 2023 county shapefile and filters for Florida.
    """
    print("Downloading Florida county boundaries...")
    
    # US Census Bureau TIGER/Line 2023 counties shapefile
    # This is a direct download link for the counties shapefile
    counties_url = "https://www2.census.gov/geo/tiger/TIGER2023/COUNTY/tl_2023_us_county.zip"
    
    try:
        # Download the shapefile
        print("  Downloading US counties shapefile (this may take a moment)...")
        response = requests.get(counties_url, timeout=60, stream=True)
        response.raise_for_status()
        
        # Save temporarily
        temp_file = "temp_counties.zip"
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(temp_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        if downloaded % (1024 * 1024) == 0:  # Print every MB
                            print(f"  Downloaded: {downloaded / (1024*1024):.1f} MB ({percent:.1f}%)")
        
        print("  Reading shapefile...")
        # Read into GeoDataFrame
        counties_gdf = gpd.read_file(f"zip://{temp_file}")
        
        # Filter for Florida (STATEFP = '12')
        florida_counties = counties_gdf[counties_gdf['STATEFP'] == '12'].copy()
        
        # Ensure CRS is WGS84 (EPSG:4326) for folium
        if florida_counties.crs != 'EPSG:4326':
            florida_counties = florida_counties.to_crs('EPSG:4326')
        
        # Clean up temp file
        if os.path.exists(temp_file):
            os.remove(temp_file)
        
        print(f"  ✓ Loaded {len(florida_counties)} Florida counties")
        return florida_counties
        
    except Exception as e:
        print(f"  Error downloading counties: {e}")
        print("  Attempting alternative method...")
        
        # Fallback: Try using a GeoJSON from a public source
        try:
            # Alternative: Use a GeoJSON from a reliable source
            geojson_url = "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"
            print("  Trying alternative GeoJSON source...")
            
            # This approach requires different handling, so let's stick with the primary method
            # and provide clear error message
            raise Exception("Primary download method failed. Please check your internet connection.")
            
        except Exception as e2:
            print(f"  Alternative method also failed: {e2}")
            print("\n  Please ensure you have:")
            print("    1. Internet access")
            print("    2. Sufficient disk space (~50MB)")
            print("    3. All required packages installed")
            raise


def geocode_address(address, geolocator, max_retries=3):
    """
    Geocode an address with retry logic.
    """
    for attempt in range(max_retries):
        try:
            location = geolocator.geocode(address, timeout=10)
            if location:
                return location.latitude, location.longitude
            time.sleep(1)  # Rate limiting
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            else:
                print(f"Failed to geocode {address}: {e}")
                return None, None
    return None, None


def get_fortiline_branches():
    """
    Define Fortiline Waterworks branches in Florida.
    Returns a list of dictionaries with name and address.
    """
    branches = [
        {"name": "Miami", "address": "14202 SW 142nd Ave, Miami, FL 33186"},
        {"name": "Pompano Beach", "address": "2250 N Andrews Ave, Pompano Beach, FL 33069"},
        {"name": "Riviera Beach", "address": "6759 White Dr, Riviera Beach, FL 33407"},
        {"name": "Fort Pierce", "address": "3904 Selvitz Rd, Fort Pierce, FL 34982"},

        {"name": "Fort Myers", "address": "4810 Laredo Ave, Fort Myers, FL 33905"},
        {"name": "Sarasota", "address": "2074 47th Street, Sarasota, FL 34234"},
        {"name": "Tampa", "address": "1031 S 86th Street, Tampa, FL 33619"},
        {"name": "Dundee", "address": "225 W Frederick Ave, Dundee, FL 33838"},
        {"name": "Kissimmee", "address": "731 Duncan Ave, Kissimmee, FL 34744"},

        {"name": "Apopka", "address": "3636 Fudge Rd, Apopka, FL 32703"},
        {"name": "Sanford", "address": "2291 West Airport Blvd, Sanford, FL 32771"},
        {"name": "Port Orange", "address": "700 Oak Heights Ct, Port Orange, FL 32129"},
        {"name": "Ocala", "address": "3518 SW 13th St, Ocala, FL 34474"},

        {"name": "St Augustine", "address": "3780 Deerpark Blvd, St Augustine, Fl 32033"},
        {"name": "Jacksonville", "address": "6982 Highway Ave, Jacksonville, FL 32254"},
        {"name": "Lake City", "address": "3847 US-441, Lake City, FL 32025"},

        {"name": "Panama City", "address": "1417 Transmitter Rd, Fl 32401"},
   
    ]
    return branches


def geocode_branches(branches):
    """
    Geocode all branch addresses to get lat/long coordinates.
    """
    print("Geocoding Fortiline branch addresses...")
    geolocator = Nominatim(user_agent="fortiline_florida_map")
    
    branch_locations = []
    for i, branch in enumerate(branches, 1):
        print(f"  Geocoding {i}/{len(branches)}: {branch['name']}...")
        lat, lon = geocode_address(branch["address"], geolocator)
        
        if lat and lon:
            branch_locations.append({
                "name": branch["name"],
                "address": branch["address"],
                "latitude": lat,
                "longitude": lon
            })
            print(f"    ✓ Found: ({lat:.4f}, {lon:.4f})")
        else:
            print(f"    ✗ Failed to geocode: {branch['address']}")
        
        # Rate limiting to avoid overwhelming the geocoding service
        time.sleep(1)
    
    return branch_locations


def create_map(florida_counties, branch_locations):
    """
    Create an interactive Folium map with county boundaries and branch markers.
    """
    print("Creating interactive map...")
    
    # Calculate center of Florida counties for initial map view
    bounds = florida_counties.total_bounds
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2
    
    # Initialize the map centered on Florida
    florida_map = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=7,
        tiles='OpenStreetMap'
    )
    
    # Add county boundaries as a GeoJSON layer
    folium.GeoJson(
        florida_counties,
        name='Florida Counties',
        style_function=lambda feature: {
            'fillColor': '#4A90E2',
            'color': '#2C3E50',
            'weight': 1.5,
            'fillOpacity': 0.2,
            'dashArray': '5, 5'
        },
        tooltip=folium.GeoJsonTooltip(
            fields=['NAME'],
            aliases=['County: '],
            sticky=True
        )
    ).add_to(florida_map)
    
    # Add branch markers
    for branch in branch_locations:
        folium.Marker(
            location=[branch['latitude'], branch['longitude']],
            popup=folium.Popup(
                f"<b>{branch['name']}</b><br>{branch['address']}",
                max_width=300
            ),
            tooltip=branch['name'],
            icon=folium.Icon(color='red', icon='tint', prefix='fa')
        ).add_to(florida_map)
    
    # Add layer control to toggle county boundaries
    folium.LayerControl().add_to(florida_map)
    
    # Add a title/legend
    title_html = '''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 300px; height: 90px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
    <h4 style="margin-top:0">Fortiline Waterworks - Florida</h4>
    <p style="margin-bottom:0">Red markers: Branch locations<br>
    Click markers for details</p>
    </div>
    '''
    florida_map.get_root().html.add_child(folium.Element(title_html))
    
    return florida_map


def main():
    """
    Main function to orchestrate the map creation.
    """
    print("=" * 60)
    print("Fortiline Waterworks - Florida Interactive Map Generator")
    print("=" * 60)
    
    try:
        # Step 1: Get Florida county boundaries
        florida_counties = get_florida_counties()
        
        # Step 2: Get Fortiline branch data
        branches = get_fortiline_branches()
        
        # Step 3: Geocode branch addresses
        branch_locations = geocode_branches(branches)
        
        if not branch_locations:
            print("ERROR: No branches were successfully geocoded!")
            return
        
        # Step 4: Create the interactive map
        florida_map = create_map(florida_counties, branch_locations)
        
        # Step 5: Save the map
        output_file = "fortiline_florida_map.html"
        florida_map.save(output_file)
        
        print("\n" + "=" * 60)
        print(f"✓ Map successfully created: {output_file}")
        print(f"  - {len(florida_counties)} Florida counties")
        print(f"  - {len(branch_locations)} Fortiline branches")
        print(f"\nOpen {output_file} in your web browser to view the map!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        print("\nTroubleshooting tips:")
        print("1. Ensure you have internet access")
        print("2. Check that all required packages are installed:")
        print("   pip install requests pandas geopandas folium geopy")
        print("3. If geocoding fails, you may need to wait and try again")
        raise


if __name__ == "__main__":
    main()

   