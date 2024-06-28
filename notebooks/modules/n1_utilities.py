import netCDF4 as nc
import xarray as xr
import dask
import numpy as np
import pandas as pd
import glob
import os
import cftime
import folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import time
import json


def read_json_to_dict(file_name, sort=False):
    """
    Reads a JSON file from a directory relative to the script's location, sorts its keys (countries) 
    and their subkeys (subareas) alphabetically if requested, and returns its contents as a dictionary.

    Parameters:
    file_name (str): The name of the JSON file.
    sort (bool): A flag to determine whether to sort the dictionary alphabetically by countries and subareas.

    Returns:
    dict: The contents of the JSON file, optionally sorted.
    """
    # Construct the file path relative to the current script's directory
    current_dir = os.path.dirname(__file__)
    file_path = os.path.join(current_dir, '..', 'data', file_name)
    
    # Load the data from the JSON file
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    # Sort the countries and subareas alphabetically if sorting is enabled
    if sort:
        sorted_data = {country: sorted(subareas) for country, subareas in sorted(data.items())}
        return sorted_data
    
    return data



def adjust_to_nearest_025(coord):
    """
    Adjust the given coordinate value to the nearest multiple of 0.25.
    
    Args:
    coord (float): The coordinate value to adjust.
    
    Returns:
    float: Adjusted coordinate value, rounded to the nearest multiple of 0.25.
    """
    return np.round(coord * 4) / 4



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
    adjusted_start = adjust_to_nearest_025(start_coord)
    adjusted_end = adjust_to_nearest_025(end_coord)
    adjusted_start, adjusted_end = min(adjusted_start, adjusted_end), max(adjusted_start, adjusted_end)     # Ensure start is less than end
    coordinate_values = np.arange(adjusted_start, adjusted_end + 0.25, 0.25)      # Generate values within the range
    return coordinate_values.tolist()



def display_map(bounds):
    """
    Create a map with a rectangle representing the bounding box.
    
    Parameters:
    bounds (list): A list containing the coordinates of the bounding box 
                   in the format [min_lat, max_lat, min_lon, max_lon].
    
    Returns:
    folium.Map: A folium map object with the bounding box displayed.
    
    Note:
    This map is to verify that the selected area is the one of interest
    """
    # Create a map centered around the middle of the bounds
    center_lat = (bounds[0] + bounds[1]) / 2
    center_lon = (bounds[2] + bounds[3]) / 2
    folium_map = folium.Map(location=[center_lat, center_lon], zoom_start=6)
    
    # Add a rectangle to represent the bounding box
    folium.Rectangle(
        bounds=[(bounds[0], bounds[2]), (bounds[1], bounds[3])],
        color='blue',
        fill=True,
        fill_opacity=0.5
    ).add_to(folium_map)    
    return folium_map



def preprocess(ds, bounds):
    """
    Subset the dataset to the specified geographic bounds.

    Parameters:
    ds (xarray.Dataset): The dataset to be subsetted.
    bounds (list): A list containing the coordinates of the bounding box 
                   in the format [min_lon, min_lat, max_lon, max_lat].

    Returns:
    xarray.Dataset: The subsetted dataset.
    """
    min_lon, min_lat, max_lon, max_lat = bounds
    latitude_list = generate_coordinate_values(min_lat, max_lat)
    longitude_list = generate_coordinate_values(min_lon, max_lon)
    ds_subset = ds.sel(lat=latitude_list, lon=longitude_list)
    return ds_subset



def is_readable_nc(file_path):
    """
    Check if a NetCDF file is readable.

    This function attempts to open a NetCDF file in read-only mode to determine if it is accessible and not corrupted.
    It handles any errors encountered during the file opening process and reports if the file is unreadable.

    Parameters:
    file_path (str): The path to the NetCDF file to be checked.

    Returns:
    bool: True if the file can be successfully opened, False otherwise.

    Notes:
    - The function uses a try-except block to handle potential OSError exceptions that may occur if the file is 
      corrupted or otherwise unreadable.
    - If an error occurs, a warning message is printed, indicating the file path of the unreadable file.
    """
    try:
        with nc.Dataset(file_path, 'r') as dataset:
            pass  # Just attempting to open the file
        return True
    except OSError:
        print(f"Warning: Skipping unreadable NetCDF file: {file_path}")
        return False

    

            
def handle_area_change(bounds, selected_month, selected_timescale):
    """
    Load and process a dataset of climate data for a specified month and geographic area.

    This function constructs a file path to locate NetCDF files corresponding to a specific month, 
    filters these files to include only those that are readable, and then loads them as an xarray 
    dataset. The dataset is processed to focus on the geographical bounds specified.

    Parameters:
    bounds (tuple): A tuple representing the geographic boundary coordinates, where the expected 
                    format is (min_longitude, min_latitude, max_longitude, max_latitude).
    selected_month (str): A string representing the month for which the data is to be loaded, in two-digit format (e.g., "01" for January).
    selected_timescale (str): A string representing the timescale for which the data is to be loaded.
    
    Returns:
    xarray.Dataset or None: The processed dataset containing climate data for the specified area and month, 
                            or None if no readable files are found.

    Raises:
    FileNotFoundError: If no files match the expected pattern for the specified month in the data directory.

    Notes:
    - Assumes the presence of the function `is_readable_nc(file)` that checks the readability of each NetCDF file.
    - Utilizes the `preprocess` function to apply additional data processing for the specified bounds
    - The dataset loading is parallelized to enhance performance.
    """
    data_path = f'/data1/drought_dataset/spei/spei{selected_timescale}/'
    file_pattern = f'SPEI{selected_timescale}_*{selected_month}.nc'
    file_list = sorted(glob.glob(os.path.join(data_path, file_pattern)))
    # Filter files to include only those that are readable
    valid_files = [file for file in file_list if is_readable_nc(file)]
    if not valid_files:
        print("No readable NetCDF files found.")
        return None

    # Load and process the dataset
    data = xr.open_mfdataset(
        valid_files,
        concat_dim='time',
        combine='nested',
        parallel=True,
        preprocess=lambda ds: preprocess(ds, bounds)  # Ensure preprocess function is defined to handle bounds
    )
    print("Data loaded and processed for the selected area and month.")
    return data





def get_country_bounds(country):
    """
    Retrieve the bounding box coordinates for a given country.

    Parameters:
    country (str): The name of the country for which to retrieve the bounding box.

    Returns:
    tuple or str: A tuple containing the bounding box coordinates in the format 
                  (min_lat, max_lat, min_lon, max_lon) if successful, 
                  or an error message if not.
    """
    geolocator = Nominatim(user_agent="talesofdrought")     # Initialize the Nominatim client
    try:
        # Use geocode to query the country with the parameter for getting bounding box
        location = geolocator.geocode(country, exactly_one=True, timeout=10)
        if location:
            # Extract the bounding box
            bounding_box = location.raw['boundingbox']
            bounds = (float(bounding_box[0]), float(bounding_box[1]),
                      float(bounding_box[2]), float(bounding_box[3]))
            return bounds
        else:
            return "No data found."
    except GeocoderTimedOut:
        print(f"Geocoding timed out for {country}; retrying...")
        time.sleep(1)
        return get_country_bounds(country)  # Retry for this country
    except Exception as e:
        return f"Error retrieving data for {country}: {e}"

    
    
def update_subarea_selector(change, placeholder_country, placeholder_subarea, subarea_selector, country_to_subareas):
    """
    Update the options of a subarea selector widget based on the selected country from a related selector widget.

    This function is bound to the country selector widget to handle its change events. It updates the subarea
    selector's options dynamically based on the country selected. If the default placeholder country is selected, 
    it resets the subarea selector to its placeholder state.

    Parameters:
    change (dict): A dictionary containing details of the change event, with keys 'type', 'name', and 'new', where 
                   'new' is the newly selected country value.
    placeholder_country (str): The placeholder text or value for the country selector, indicating no country selected.
    placeholder_subarea (str): The placeholder text or value for the subarea selector, indicating no subarea selected.
    subarea_selector (widget): The widget instance of the subarea selector to be updated.
    country_to_subareas (dict): A dictionary mapping country names to a list of their respective subareas.

    Notes:
    - The function expects to be triggered by a change event from a widget where
      the 'type' of the event is 'change' and the 'name' is 'value'.
    - Debug statements are used to log the currently selected country and subareas, aiding in troubleshooting.
    """
    if change['type'] == 'change' and change['name'] == 'value':
        new_country = change['new']
        print("Country selected:", new_country)  # Debug: Check selected country
        if new_country != placeholder_country:
            subareas = country_to_subareas.get(new_country, [])
            print("Subareas found:", subareas)  # Debug: List subareas found
            subarea_selector.options = [placeholder_subarea] + subareas
        else:
            subarea_selector.options = [placeholder_subarea]
            print("Reset subarea selector due to country placeholder selection")  # Debug: Resetting subarea selector




def update_display(country_selector, subarea_selector, month_selector, timescale_selector, months, timescales, placeholder_country, placeholder_subarea, placeholder_month, placeholder_timescale):
    """
    Update the area subset data based on selected values from country, month, and subarea selectors.

    Parameters:
    country_selector (ipywidgets.Widget): Widget for selecting a country.
    subarea_selector (ipywidgets.Widget): Widget for selecting a subarea.
    month_selector (ipywidgets.Widget): Widget for selecting a month.
    months (dict): Dictionary of months mapping month names to values.
    placeholder_country (str): Placeholder text for no country selection.
    placeholder_month (str): Placeholder text for no month selection.
    placeholder_subarea (str): Placeholder text for no subarea selection.
    placeholder_timescale (str): Placeholder text for no timescale selection.
    Returns:
    xarray.Dataset or None: The dataset containing climate data for a specific area and month, or None if no data is available.
    """
    global area_subset_data  # Make sure to declare this if it's supposed to be global
    if country_selector.value != placeholder_country and subarea_selector.value != placeholder_subarea and month_selector.value != placeholder_month and timescale_selector.value != placeholder_timescale:
        bounds = get_country_bounds(country_selector.value)
        if subarea_selector.value != placeholder_subarea:
            bounds = get_country_bounds(subarea_selector.value)
        selected_month = months.get(month_selector.value, "01")  # Default to January if not properly selected
        selected_timescale = timescales.get(timescale_selector.value, "12")  # Default to 12 months if not properly selected
        area_subset_data = handle_area_change(bounds, selected_month, selected_timescale)
        if area_subset_data is not None:
            print("Data updated for selected area and month")
        else:
            print("No data available for the selected area and month.")
        return area_subset_data

    
    
def assign_color_spei(spei_values):
    """
    Assigns colors based on the Standardized Precipitation-Evapotranspiration Index (SPEI) values.

    This function takes a list of SPEI values and assigns a color code to each value based on the degree of wetness or dryness.
    The colors are assigned as follows:
    - Extremely wet: SPEI > 2.0 (color: '#064A78')
    - Severely wet: 1.5 < SPEI <= 2.0 (color: '#49AEFF')
    - Moderately wet: 1.0 < SPEI <= 1.5 (color: '#61A5CE')
    - Near-normal / mildly wet: 0 < SPEI <= 1.0 (color: '#ACD1E5')
    - Near-normal / mildly dry: -1.0 < SPEI <= 0 (color: '#F7BB9F')
    - Moderately dry: -1.5 < SPEI <= -1.0 (color: '#D96C59')
    - Severely dry: -2.0 < SPEI <= -1.5 (color: '#AF2331')
    - Extremely dry: SPEI <= -2.0 (color: '#681824')

    Parameters:
    spei_values (list of float): A list of SPEI values to be evaluated.

    Returns:
    list of str: A list of color codes corresponding to the SPEI values.
    """
    colors = []
    for spei in spei_values:
        if spei > 2.0:
            colors.append('#064A78')  # extremely wet
        elif 1.5 < spei <= 2.0:
            colors.append('#49AEFF')  # severely wet
        elif 1.0 < spei <= 1.5:
            colors.append('#61A5CE')  # moderately wet
        elif 0 < spei <= 1.0:
            colors.append('#ACD1E5')  # near-normal / mildly wet
        elif -1.0 < spei <= 0:
            colors.append('#F7BB9F')  # near-normal / mildly dry
        elif -1.5 < spei <= -1.0:
            colors.append('#D96C59')  # moderately dry
        elif -2.0 < spei <= -1.5:
            colors.append('#AF2331')  # severely dry
        else:
            colors.append('#681824')  # extremely dry
    return colors

