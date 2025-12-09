import netCDF4 as nc
import numpy as np
import json
import os
import requests
import folium
from IPython.display import display, IFrame
from utils.widgets_handler import get_adm_level_and_area_name


def get_isocode_for_country(country_list, country_name):
    """
    Retrieve the ISO code for a given country name.

    Parameters:
    country_list (list): List of country dictionaries.
    country_name (str): Name of the country.

    Returns:
    str: ISO code of the country or None if not found.
    """
    return next((item['isocode'] for item in country_list if item["name"] == country_name), None)



def fetch_geojson_data(base_url, isocode, adm_level, selected, selected_area):
    """
    Fetch the GeoJSON data from the geoboundaries API.

    Parameters:
    base_url (str): The base URL of the geoboundaries API.
    isocode (str): ISO code of the country.
    adm_level (str): The administrative level.
    selected (dict): Dictionary containing selected values for various parameters.
    selected_area (str): Name of the selected area.

    Returns:
    dict: GeoJSON data for the selected area.
    """
    api_url = f"{base_url}/{isocode}/{adm_level}/"
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        geojson_url = data['simplifiedGeometryGeoJSON']
        return download_geojson_data(geojson_url)
    else:
        print(f"No data available for {selected_area} at {adm_level}, checking lower administrative levels.")
        return handle_fallbacks(adm_level, selected)

    

def download_geojson_data(geojson_url):
    """
    Download the GeoJSON data from the provided URL.

    Parameters:
    geojson_url (str): URL of the GeoJSON data.

    Returns:
    dict: GeoJSON data or None if download fails.
    """
    geojson_response = requests.get(geojson_url)
    if geojson_response.status_code == 200:
        return geojson_response.json()
    else:
        print("Failed to download GeoJSON data.")
        return None


    
def display_map(bounds, zoom_start=8):
    """
    Create a map with a rectangle representing the bounding box.
    
    Parameters:
    bounds (tuple): A tuple containing the coordinates of the bounding box 
                   in the format (min_lon, min_lat, max_lon, max_lat).
    
    Returns:
    folium.Map: A folium map object with the bounding box displayed.
    
    Note:
    This map is to verify that the selected area is the one of interest
    """
    min_lon, min_lat, max_lon, max_lat = bounds
    
    # Create a map centered around the middle of the bounds
    center_lat = (min_lat + max_lat) / 2
    center_lon = (min_lon + max_lon) / 2
    folium_map = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_start)
    
    # Add a rectangle to represent the bounding box
    folium.Rectangle(
        bounds=[(min_lat, min_lon), (max_lat, max_lon)],
        color='blue',
        fill=True,
        fill_opacity=0.5
    ).add_to(folium_map)
    
    return folium_map



def display_map_in_iframe(folium_map, width=500, height=500):
    """
    Embeds a Folium map in an iframe for controlled size display in Jupyter Notebooks.
    
    Parameters:
    folium_map (folium.Map): The Folium map object to be displayed.
    width (int): Width of the iframe.
    height (int): Height of the iframe.
    
    Returns:
    IPython.display.IFrame: An iframe containing the HTML representation of the Folium map.
    """
    map_html = 'map.html'
    folium_map.save(map_html)
    return IFrame(map_html, width=width, height=height)



def handle_fallbacks(adm_level, selected):
    """
    Handle fallbacks to lower administrative levels if data is not available.

    Parameters:
    adm_level (str): The current administrative level.
    selected (dict): Dictionary containing selected values for various parameters.

    Returns:
    dict: GeoJSON data or None if no data is available.
    """
    if adm_level == 'ADM2':
        return get_boundaries({**selected, 'adm2_subarea': None}, country_list, placeholders)  # Fallback to ADM1
    elif adm_level == 'ADM1':
        return get_boundaries({**selected, 'adm1_subarea': None}, country_list, placeholders)  # Fallback to ADM0
    return None





def get_boundaries(selected, country_list, placeholders):
    """
    Fetch geographic boundaries data for the selected area and return standardized coordinates.

    This function retrieves the geographic boundaries for a selected area based on the administrative
    level (ADM0, ADM1, ADM2) and returns a uniformly structured list of coordinates for the area's geometry.

    Parameters:
    selected (dict): Dictionary containing selected values for various parameters including:
                     - 'country': Name of the selected country.
                     - 'adm': Administrative level (ADM0, ADM1, ADM2).
    country_list (list): List of dictionaries containing country information with keys 'name' and 'iso_code'.
    placeholders (dict): Dictionary containing placeholder values to check against when selections are default or empty.

    Returns:
    list: A uniformly structured list of coordinates for the selected area's geometry.

    Notes:
    - The function determines the administrative level and selected area name.
    - It fetches the ISO code for the selected country from the provided country list.
    - It retrieves the GeoJSON data from the GeoBoundaries API based on the ISO code and administrative level.
    - The function processes the GeoJSON data to extract and return the coordinates of the selected area.
    """
    base_url = "https://www.geoboundaries.org/api/current/gbOpen"
    coordinates = []

    adm_level, selected_area = get_adm_level_and_area_name(selected, placeholders)
    if adm_level:
        isocode = get_isocode_for_country(country_list, selected['country'])
        if isocode:
            full_geojson = fetch_geojson_data(base_url, isocode, adm_level, selected, selected_area)
            if full_geojson:
                for feature in full_geojson['features']:
                    if (adm_level == 'ADM0' and feature['properties']['shapeGroup'] == isocode) or \
                       (adm_level in ['ADM1', 'ADM2'] and feature['properties']['shapeName'] == selected_area):
                        geom_type = feature['geometry']['type']
                        coords = feature['geometry']['coordinates']

                        if geom_type == 'Polygon':
                            coordinates.append(coords)  # Keep Polygon coordinates as is
                        elif geom_type == 'MultiPolygon':
                            for coord in coords:
                                coordinates.extend(coord)  # Flatten MultiPolygon coordinates to a single list
                        break
                if coordinates:
                    print(f"Coordinates retrieved for {selected_area} ({adm_level}) - {base_url}/{isocode}/{adm_level}/")
                else:
                    print("No matching area found within the GeoJSON.")
            else:
                print("Failed to retrieve GeoJSON data.")
        else:
            print("Invalid ISO code.")
    else:
        print("No valid administrative level selected.")
    return coordinates




def calculate_bounding_box(coordinates):
    """
    Calculate the bounding box from a list of coordinate tuples.

    This function takes a list of coordinates, which may be nested at varying levels, and calculates
    the bounding box that contains all the points. The bounding box is adjusted to the nearest grid points.

    Parameters:
    coordinates (list): A list of lists of tuples containing coordinates (longitude, latitude).
                        The structure can be irregular with varying levels of nesting.

    Returns:
    tuple: A tuple containing the coordinates of the bounding box in the format 
           (min_lon, min_lat, max_lon, max_lat).

    Example:
    >>> coordinates = [
    ...     [[[-8.668909, 28.714092], [-8.668908, 28.30392], ...]],
    ...     [[16.535271061257447, 46.996895243634015], ...]
    ... ] 
    or
    >>> coordinates = [
    ...    [[[[-8.668909, 28.714092], [-8.668908, 28.30392], ...]],
    ...     [[16.535271061257447, 46.996895243634015], ...]
    ... ]]
    >>> calculate_bounding_box(coordinates)
    (-8.668909, 21.651657, 11.728914, 36.951959)

    Notes:
    - The function handles irregular nesting levels in the input coordinates.
    - The coordinates are first converted to a NumPy array and then flattened.
    - The minimum and maximum longitude and latitude values are computed.
    - The values are adjusted to the nearest grid points using `nearest_grid_point` function.
    """
    # Convert to numpy array for efficient processing and flatten
    all_coords = np.vstack([np.array(sublist).reshape(-1, 2) for sublist in coordinates])

    # Debug: Print the first few flattened coordinates to verify structure
    # print("First 10 Flattened Coordinates:", all_coords[:10])

    # Validate the structure of the flattened coordinates
    if all_coords.ndim != 2 or all_coords.shape[1] != 2:
        raise ValueError("Flattened coordinates should be a 2D array with shape (n, 2).")

    # Calculate the min and max values for longitude and latitude
    min_lon = np.min(all_coords[:, 0])
    max_lon = np.max(all_coords[:, 0])
    min_lat = np.min(all_coords[:, 1])
    max_lat = np.max(all_coords[:, 1])

    # Debug: Print the calculated min and max values
    # print("\nCalculated Min/Max Values:")
    # print(f"Min Longitude: {min_lon}, Max Longitude: {max_lon}")
    # print(f"Min Latitude: {min_lat}, Max Latitude: {max_lat}")

    # Adjust to nearest grid points (assuming this function is correctly defined)
    adjusted_min_lon = nearest_grid_point(min_lon)
    adjusted_max_lon = nearest_grid_point(max_lon)
    adjusted_min_lat = nearest_grid_point(min_lat)
    adjusted_max_lat = nearest_grid_point(max_lat)

    # Debug: Print the adjusted values
    # print("\nAdjusted Min/Max Values:")
    # print(f"Adjusted Min Longitude: {adjusted_min_lon}, Adjusted Max Longitude: {adjusted_max_lon}")
    # print(f"Adjusted Min Latitude: {adjusted_min_lat}, Adjusted Max Latitude: {adjusted_max_lat}")

    return (adjusted_min_lon, adjusted_min_lat, adjusted_max_lon, adjusted_max_lat)



            
def nearest_grid_point(coord, grid_resolution=0.25):
    """
    Adjust the given coordinate value to the nearest multiple of 0.25.
    
    Args:
    coord (float): The coordinate value to adjust.
    
    Returns:
    float: Adjusted coordinate value, rounded to the nearest multiple of 0.25.
    """
    return np.round(coord / grid_resolution) * grid_resolution
     
        

def generate_coordinate_values(start_coord, end_coord):
    """
    Generate a list of coordinate values from start to end, adjusted to the nearest 0.25 increment.
    
    Args:
    start_coord (float): The starting coordinate.
    end_coord (float): The ending coordinate.
    
    Returns:
    list: A list of coordinates from start to end, adjusted to 0.25 increments.
    
    Note:
    This function is because ds.sel(lat=slice(min_lat, max_lat), lon=slice(min_lon, max_lon)) seems not working
    """
    adjusted_start = nearest_grid_point(start_coord)
    adjusted_end = nearest_grid_point(end_coord)
    adjusted_start, adjusted_end = min(adjusted_start, adjusted_end), max(adjusted_start, adjusted_end)     # Ensure start is less than end
    coordinate_values = np.arange(adjusted_start, adjusted_end + 0.25, 0.25)      # Generate values within the range
    return coordinate_values.tolist()

