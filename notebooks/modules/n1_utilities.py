import netCDF4 as nc
import xarray as xr
import dask
import math
import numpy as np
import pandas as pd
import json
import glob
import os
import requests
import time
from datetime import datetime
import cftime
from IPython.display import display, IFrame
import plotly.graph_objects as go



def get_file_path(file_name):
    """
    Get the file path for the given file name.

    Args:
    file_name (str): The name of the file.

    Returns:
    str: The file path for the given file name.
    """
    current_dir = os.path.dirname(__file__)
    return os.path.join(current_dir, '..', 'data', file_name)



def save_selection(selection):
    """
    Save the current selection to a JSON file.

    Parameters:
    selection (dict): A dictionary containing the current selections of country, subarea, month, year, and timescale.
    """
    file_path = get_file_path('selection.json')
    with open(file_path, 'w') as file:
        json.dump(selection, file)
        

        
def read_json_to_dict(file_name):
    """
    Reads a JSON file and returns its content as a dictionary.

    Args:
    file_name (str): The name of the JSON file.

    Returns:
    dict: The content of the JSON file as a dictionary.
    """
    file_path = get_file_path(file_name)
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except json.JSONDecodeError:
        print(f"Error decoding JSON in file: {file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")
        

        
def sort_dict_list(lst):
    """
    Recursively sorts lists of dictionaries by the 'name' key and sorts nested levels.

    Args:
    lst (list): The list of dictionaries to be sorted.

    Returns:
    list: The sorted list of dictionaries.
    """
    sorted_list = sorted(lst, key=lambda x: x['name'])
    for item in sorted_list:
        for key, value in item.items():
            if isinstance(value, list) and value and isinstance(value[0], dict):
                item[key] = sort_dict_list(value)
    return sorted_list



def read_json_to_sorted_dict(file_name):
    """
    Reads a JSON file, sorts all nested levels alphabetically by the 'name' key, 
    and returns the content as a sorted list.

    Args:
    file_name (str): The name of the JSON file.

    Returns:
    list: The sorted content of the JSON file.
    """
    file_path = get_file_path(file_name)
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        
        sorted_data = sort_dict_list(data)
        return sorted_data
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except json.JSONDecodeError:
        print(f"Error decoding JSON in file: {file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")




def get_subareas_for_country(country_list, isocode, level='adm1_subareas'):
    """
    Retrieve the names of subareas for a given country identified by its ISO code.

    Args:
    country_list (list): A list of country dictionaries.
    isocode (str): The ISO code of the country.
    level (str, optional): The key in the country dictionary that contains the subareas. Default is 'adm1_subareas'.

    Returns:
    list: A list of subarea names. Returns an empty list if the country or subareas are not found.
    """
    for country in country_list:
        if country['isocode'] == isocode:
            return [subarea['name'] for subarea in country.get(level, [])]
    return []




def update_subareas(change, country_list, placeholders, adm1_subarea_selector, adm2_subarea_selector):
    """
    Update the subarea selectors based on the selected country.

    Args:
    change (dict): The change event dictionary containing the type and name of the change.
    country_list (list): A list of country dictionaries.
    placeholders (dict): A dictionary containing placeholder texts for the selectors.
    adm1_subarea_selector (object): The selector object for adm1 subareas.
    adm2_subarea_selector (object): The selector object for adm2 subareas.
    """
    if change['type'] == 'change' and change['name'] == 'value':
        # Clear previous subarea selections
        selected_country = next((item for item in country_list if item["name"] == change['new']), None)
        if selected_country:
            adm1_options = get_subareas_for_country(country_list, selected_country['isocode'], 'adm1_subareas')
            adm2_options = get_subareas_for_country(country_list, selected_country['isocode'], 'adm2_subareas')
        else:
            adm1_options = []
            adm2_options = []

        # Update options with condition to show 'No subareas' message
        if adm1_options:
            adm1_subarea_selector.options = [placeholders['adm1_subarea']] + adm1_options
        else:
            adm1_subarea_selector.options = ['No adm1 subareas']

        if adm2_options:
            adm2_subarea_selector.options = [placeholders['adm2_subarea']] + adm2_options
        else:
            adm2_subarea_selector.options = ['No adm2 subareas']


            

def month_year_interaction(change, month_selector, year_selector, selected, placeholders):
    """
    Handle interactions between the month and year selectors, resetting the other selector
    when one is changed, or resetting both if neither is explicitly changed.

    Args:
    change (dict): The change event dictionary containing the owner and new value of the change.
    month_selector (object): The selector object for months.
    year_selector (object): The selector object for years.
    selected (dict): A dictionary storing the currently selected month and year.
    placeholders (dict): A dictionary containing placeholder texts for the selectors.
    """
    if change['owner'] == month_selector and change['new']:
        year_selector.value = placeholders['year']
        selected['year'] = placeholders['year']
    elif change['owner'] == year_selector and change['new']:
        month_selector.value = placeholders['month']
        selected['month'] = placeholders['month']
    else:  # year_range case
        year_selector.value = placeholders['year']
        selected['year'] = placeholders['year']
        month_selector.value = placeholders['month']
        selected['month'] = placeholders['month']        
        
        
            
def update_selected_values(selected, selectors, placeholders):
    """
    Update the selected dictionary with current values from the selectors.

    Args:
    selected (dict): A dictionary storing the currently selected values.
    selectors (dict): A dictionary containing selector objects for various fields.
    placeholders (dict): A dictionary containing placeholder texts for the selectors.
    """
    selected.update({
        'country': selectors['country'].value if selectors['country'].value != placeholders['country'] else placeholders['country'],
        'adm1_subarea': selectors['adm1_subarea'].value if (selectors['adm1_subarea'].value != placeholders['adm1_subarea']) and \
        (selectors['adm1_subarea'].value != 'No adm1 subareas') else placeholders['adm1_subarea'],
        'adm2_subarea': selectors['adm2_subarea'].value if (selectors['adm2_subarea'].value != placeholders['adm2_subarea']) and \
        (selectors['adm2_subarea'].value != 'No adm2 subareas') else placeholders['adm2_subarea'],
        'timescale': selectors['timescale'].value if selectors['timescale'].value != placeholders['timescale'] else placeholders['timescale'],
        'month': selectors['month'].value if selectors['month'].value != placeholders['month'] else placeholders['month'],
        'year': selectors['year'].value if selectors['year'].value != placeholders['year'] else placeholders['year'],
        'year_range': selectors['year_range'].value
    })
    



def find_missing_selections(btn_name, selected, placeholders):
    """
    Find any missing selections based on the current state of the selected dictionary.

    Args:
    btn_name (str): The name of the button clicked to trigger the validation.
    selected (dict): A dictionary storing the currently selected values.
    placeholders (dict): A dictionary containing placeholder texts for the selectors.

    Returns:
    list: A list of missing selections.
    """
    missing = []
    if selected['country'] == placeholders['country']:
        missing.append('country')
    if selected['timescale'] == placeholders['timescale']:
        missing.append('timescale')

    if btn_name == 'month_widgets_btn' and selected['month'] == placeholders['month']:
        missing.append('month')
    elif btn_name == 'year_widgets_btn' and selected['year'] == placeholders['year']:
        missing.append('year')
    elif btn_name == 'year_range_widgets_btn' and selected['year_range'] is None:
        missing.append('year range')

    return missing


def display_missing_alert(output_area, missing):
    """
    Display an alert in the output area for any missing selections.

    Args:
    output_area (object): The output area object for displaying messages.
    missing (list): A list of missing selections.
    """
    with output_area:
        output_area.clear_output()
        alert = "Please select a value for " + ", ".join(missing)
        print(alert)




def validate_selections(btn_name, selected, selectors, placeholders, output_area):
    """
    Validate the current selections and update the selected dictionary.

    Args:
    btn_name (str): The name of the button clicked to trigger the validation.
    selected (dict): A dictionary storing the currently selected values.
    selectors (dict): A dictionary containing selector objects for various fields.
    placeholders (dict): A dictionary containing placeholder texts for the selectors.
    output_area (object): The output area object for displaying messages.

    Returns:
    bool: True if all required selections are made, False otherwise.
    """
    update_selected_values(selected, selectors, placeholders)
    save_selection(selected)
    missing = find_missing_selections(btn_name, selected, placeholders)

    if missing:
        display_missing_alert(output_area, missing)
        return False
    return True





def get_period_of_time(btn_name, selected, placeholders):
    """
    Determines the string representing the selected time period based on the button name.

    Parameters:
    btn_name (str): Identifies which button was clicked.
    selected (dict): Dictionary containing selected values for various parameters.
    placeholders (dict): Placeholder values to check against when selections are default or empty.

    Returns:
    str: Description of the selected time period.
    """
    if btn_name == 'month_widgets_btn':
        time_period = 'month ' + (selected['month'] if selected['month'] != placeholders['month'] else 'undefined month')
    elif btn_name == 'year_widgets_btn':
        time_period = 'year ' + (selected['year'] if selected['year'] != placeholders['year'] else 'undefined year')
    elif btn_name == 'year_range_widgets_btn':
        start_year, end_year = selected['year_range'] if selected['year_range'] else ('undefined', 'undefined')
        time_period = f'year range {start_year} to {end_year}'

    return time_period



def get_adm_level_and_area_name(selected, placeholders):
    """
    Determine the appropriate administrative level to query and the selected area name.

    Parameters:
    selected (dict): Dictionary containing selected values for various parameters.
    placeholders (dict): Placeholder values to check against when selections are default or empty.

    Returns:
    tuple: A tuple containing the administrative level (str) and the selected area name (str).
    """
    adm_level = None
    if selected['adm2_subarea'] and selected['adm2_subarea'] != placeholders['adm2_subarea']:
        adm_level = 'ADM2'
        selected_area = selected['adm2_subarea']
    elif selected['adm1_subarea'] and selected['adm1_subarea'] != placeholders['adm1_subarea']:
        adm_level = 'ADM1'
        selected_area = selected['adm1_subarea']
    elif selected['country'] and selected['country'] != placeholders['country']:
        adm_level = 'ADM0'
        selected_area = selected['country']
    return adm_level, selected_area



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
    Fetch geographic boundaries data for the selected area.

    Parameters:
    selected (dict): Dictionary containing selected values for various parameters.
    country_list (list): List of country dictionaries.
    placeholders (dict): Placeholder values to check against when selections are default or empty.

    Returns:
    dict: GeoJSON data for the selected area.
    """
    base_url = "https://www.geoboundaries.org/api/current/gbOpen"
    geojson_data = None

    adm_level, selected_area = get_adm_level_and_area_name(selected, placeholders)

    if adm_level:
        isocode = get_isocode_for_country(country_list, selected['country'])
        if isocode:
            geojson_data = fetch_geojson_data(base_url, isocode, adm_level, selected, selected_area)
        else:
            print("Invalid ISO code.")
    else:
        print("No valid administrative level selected.")

    if geojson_data:
        print(f"Coordinates retrieved for {selected_area} ({adm_level}) - {base_url}/{isocode}/{adm_level}/")
    else:
        print("Failed to retrieve GeoJSON data.")
    
    return geojson_data


            
            
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


#####################################################################
    
def is_readable_nc(file_path):
    """
    Check if a NetCDF file is readable.

    Parameters:
    file_path (str): The path to the NetCDF file.

    Returns:
    bool: True if the file is readable, False otherwise.
    """
    try:
        with nc.Dataset(file_path, 'r') as dataset:
            pass  # File opened successfully
        return True
    except OSError:
        print(f"Warning: Skipping unreadable NetCDF file: {file_path}")
        return False

    
    
def preprocess(ds, bounds):
    """
    Preprocess the dataset by subsetting it within the given geographic bounds.

    Parameters:
    ds (xarray.Dataset): The dataset to preprocess.
    bounds (tuple): A tuple containing the geographic bounds (min_lon, min_lat, max_lon, max_lat).

    Returns:
    xarray.Dataset: The subset of the original dataset within the specified bounds.

    Raises:
    ValueError: If generated coordinates do not match any available in the dataset.
    """
    min_lon, min_lat, max_lon, max_lat = bounds
    latitude_list = generate_coordinate_values(min_lat, max_lat)
    longitude_list = generate_coordinate_values(min_lon, max_lon)
    # Ensure only existing coordinates are used for subsetting
    latitude_list = [lat for lat in latitude_list if lat in ds.lat.values]
    longitude_list = [lon for lon in longitude_list if lon in ds.lon.values]
    if not latitude_list or not longitude_list:
        raise ValueError("Generated coordinates do not match any available in the dataset.")    
    ds_subset = ds.sel(lat=latitude_list, lon=longitude_list)
    return ds_subset



def generate_file_patterns(btn_name, selectors, placeholders, months, selected_timescale, middle_pattern, data_path):
    """
    Generate file patterns to match NetCDF files based on the selected criteria.

    Parameters:
    btn_name (str): Button name to determine the type of data fetching.
    selectors (dict): Dictionary containing widget selectors.
    placeholders (dict): Placeholder values for widgets.
    months (dict): Dictionary of month abbreviations to numbers.
    selected_timescale (str): The selected timescale.
    middle_pattern (str): The middle pattern for file matching.
    data_path (str): The base path for data files.

    Returns:
    list: List of file patterns matching the criteria.
    """
    if btn_name == 'year_range_widgets_btn':
        start_year, end_year = selectors['year_range'].value
        file_patterns = []
        for year in range(int(start_year), int(end_year) + 1):
            for month in months.values():
                file_pattern = f'SPEI{selected_timescale}{middle_pattern}{year}{month}*.nc'
                file_patterns.extend(glob.glob(os.path.join(data_path, file_pattern)))
    else:
        selected_month = months[selectors['month'].value] if selectors['month'].value != placeholders['month'] else None
        selected_year = selectors['year'].value if selectors['year'].value != placeholders['year'] else None
        file_pattern = f'SPEI{selected_timescale}{middle_pattern}'
        file_pattern += f'{selected_year if selected_year else "????"}{selected_month if selected_month else "??"}*.nc'
        file_patterns = sorted(glob.glob(os.path.join(data_path, file_pattern)))
    
    return file_patterns

def filter_valid_nc_files(file_patterns):
    """
    Filter out valid NetCDF files from the given file patterns.

    Parameters:
    file_patterns (list): List of file patterns.

    Returns:
    list: List of valid NetCDF files.
    """
    return [file for file in file_patterns if is_readable_nc(file)]

def load_and_preprocess_dataset(valid_files, bounds):
    """
    Load and preprocess the dataset from the valid NetCDF files.

    Parameters:
    valid_files (list): List of valid NetCDF files.
    bounds (tuple): Geographic boundary coordinates.

    Returns:
    xarray.Dataset: The processed dataset.
    """
    return xr.open_mfdataset(
        valid_files,
        concat_dim='time',
        combine='nested',
        parallel=True,
        preprocess=lambda ds: preprocess(ds, bounds)
    )


def get_xarray_data(btn_name, bounds, selectors, placeholders, months, timescales):
    """
    Load and process a dataset of climate data for a specified month, year, and geographic area.

    Parameters:
    bounds (tuple): Geographic boundary coordinates.
    btn_name (str): Button name to determine the type of data fetching.
    selectors (dict): Dictionary containing widget selectors.
    placeholders (dict): Placeholder values for widgets.
    months (dict): Dictionary of month abbreviations to numbers.
    timescales (dict): Dictionary of available timescales.

    Returns:
    xarray.Dataset or None: The processed dataset or None if no readable files are found.
    """
    selected_timescale = timescales[selectors['timescale'].value]
    data_path = f'/data1/drought_dataset/spei/spei{selected_timescale}/'
    middle_pattern = '*global_era5*_moda_ref1991to2020_'
    
    file_patterns = generate_file_patterns(btn_name, selectors, placeholders, months, selected_timescale, middle_pattern, data_path)
    
    try:
        valid_files = filter_valid_nc_files(file_patterns)
        if not valid_files:
            print("No readable NetCDF files found.")
            return None

        data = load_and_preprocess_dataset(valid_files, bounds)
        return data
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


    
    
def display_data_details(selected, subset):
    """
    Displays details of the selected data and subset based on the specified index.

    Parameters:
    selected (dict): A dictionary containing selection attributes such as country, subarea, month, year, and timescale.
    subset (list of xr.DataArray): A list of xarray DataArrays containing the subset data.

    Returns:
    None: This function only prints details to the console.
    """
    print("Country: ", selected['country'])
    print("ADM1 subarea: ", selected['adm1_subarea'])
    print("ADM2 subarea: ", selected['adm2_subarea'])
    print("Month: ", selected['month'])
    print("Year: ", selected['year'])
    print("Year range: ", selected['year_range'])
    print("Timescale: ", selected['timescale'], '\n')

    print("Time values in the subset:", subset.time.values.shape[0])
    print("Latitude values in the subset:", subset.lat.values.shape[0])
    print("Longitude values in the subset:", subset.lon.values.shape[0], '\n')

    # This prints a sample of the data for the first time point and the first 5 latitudes and longitudes
    print("Data sample: ", subset.isel(time=0, lat=slice(0, 5), lon=slice(0, 5)).values)

    # Optional: Uncomment these if more detailed outputs are needed
    # print(subset[index].values)
    # print(subset[index].time)
     
               
            

def replace_invalid_values(data: pd.DataFrame, invalid_value: float = -9999.0) -> (pd.DataFrame, int, float):
    """
    Replaces specified invalid values in a pandas DataFrame with NaN (Not a Number), counts the number of replacements,
    and calculates the ratio of invalid values over the total number of values.

    Parameters:
    - data (pd.DataFrame): The input DataFrame containing possibly invalid values.
    - invalid_value (float, optional): The value to be considered as invalid and replaced. 
      Defaults to -9999.0.

    Returns:
    - pd.DataFrame: A DataFrame with invalid values replaced by NaN.
    - int: The number of invalid values replaced.
    - float: Ratio of invalid values to total values in the DataFrame.
    """
    # Create a mask to identify invalid values
    mask = data == invalid_value
    # Count invalid entries across all columns, using compute() if necessary
    if 'dask' in str(type(data)):  # Check if the DataFrame is a Dask DataFrame
        invalid_count = mask.sum().compute()  # Use Dask's compute() for Dask DataFrames
    else:
        invalid_count = mask.sum().sum()  # Sum all true values in the mask for Pandas DataFrame

    # Calculate total number of values in the DataFrame
    total_values = data.size

    # Calculate the ratio of invalid values
    invalid_ratio = invalid_count / total_values

    # Replace invalid values with NaN using where()
    clean_data = data.where(~mask, np.nan)  # Replace where mask is not True
    
    return clean_data, int(invalid_count), float(invalid_ratio)



def remove_time_duplicates(dataset: xr.DataArray) -> (xr.DataArray, int):
    """
    Removes duplicate time entries from an xarray DataArray by keeping the first occurrence
    of each time point and discarding the subsequent duplicates. Also returns the number of duplicates removed.

    Parameters:
    - dataset (xr.DataArray): The input DataArray that contains a time dimension with potentially duplicated entries.

    Returns:
    - xr.DataArray: A new DataArray with the same data as the input but with duplicate time entries removed.
    - int: The number of duplicate time entries removed.
    
    Note:
    - This function is needed because the value of the variable 'time' of January 2024 is duplicated
    """
    time_series = pd.Series(dataset.time.values)
    original_count = len(time_series)
    unique_indices = time_series.drop_duplicates(keep='first').index
    new_dataset = dataset.isel(time=unique_indices)
    removed_count = original_count - len(unique_indices)
    
    return new_dataset, removed_count



def convert_cftime_to_datetime64(dataset: xr.DataArray, time_dim='time') -> (xr.DataArray, int):
    """
    Converts cftime.DatetimeGregorian objects within the specified time dimension of an xarray
    DataArray to numpy.datetime64 data types, and returns the number of conversions made.
    This conversion standardizes time representations for compatibility with broader numpy and pandas
    operations which may not support cftime types.

    Parameters:
    - dataset (xr.DataArray): The input DataArray containing time data potentially in cftime.DatetimeGregorian format.
    - time_dim (str): The name of the dimension in the DataArray that contains the time data. Default is 'time'.

    Returns:
    - xr.DataArray: A new DataArray with the time coordinates converted from cftime.DatetimeGregorian to numpy.datetime64.
    - int: The number of conversions from cftime.DatetimeGregorian to numpy.datetime64.
    
    Note:
    - This function is necessary because the values of the 'time' variable for January 2024 and Febraury 2024 are in cftime.DatetimeGregorian format.
    """
    times = dataset[time_dim].values
    conversion_count = 0
    new_times = []
    
    for t in times:
        if isinstance(t, cftime.DatetimeGregorian):
            new_times.append(np.datetime64(t.isoformat()))
            conversion_count += 1
        else:
            new_times.append(np.datetime64(t))
    
    new_data_array = dataset.assign_coords({time_dim: ('time', np.array(new_times, dtype='datetime64[ns]'))})
    
    return new_data_array, conversion_count



def process_datarray(data_array: xr.DataArray) -> (xr.DataArray, dict):
    """
    Processes an xarray DataArray through a sequence of data cleaning and transformation steps
    to ensure its usability in further analysis or modeling. This function standardizes the DataArray
    and returns the counts of cleaned, removed, and converted values.

    Parameters:
    - data_array (xr.DataArray): The input DataArray that will undergo processing.

    Returns:
    - xr.DataArray: The processed DataArray with standardized data formatting and cleaned values.
    - dict: Dictionary containing counts of cleaned, removed, and converted entries.
    """
    data_array, invalid_replaced_count, invalid_ratio = replace_invalid_values(data_array)
    data_array, duplicate_removed_count = remove_time_duplicates(data_array)
    data_array, conversion_count = convert_cftime_to_datetime64(data_array)

    return data_array, {
        'invalid_values_replaced': invalid_replaced_count,
        'invalid_ratio': invalid_ratio,
        'duplicates_removed': duplicate_removed_count,
        'cftime_conversions': conversion_count
    }



def compute_stats(data: xr.DataArray, full_stats: bool = True) -> dict:
    """
    Computes the statistics needed to create a boxplot from the SPEI data over latitude and longitude.
    These statistics include the median, lower and upper quantiles (25th and 75th percentiles), minimum, and maximum values.

    Parameters:
    data (xr.DataArray): The DataArray containing the SPEI data with dimensions including 'lat', 'lon', and 'time'.
    full_stats (bool): If True, computes all statistics. If False, computes only mean and median.

    Returns:
    dict: A dictionary containing:
        - times (np.ndarray): The array of time values.
        - means (np.ndarray): The array of mean values over the specified dimensions.
        - medians (np.ndarray): The array of median values over the specified dimensions.
        - q1s (np.ndarray): The array of 25th percentile values (only if full_stats is True).
        - q3s (np.ndarray): The array of 75th percentile values (only if full_stats is True).
        - mins (np.ndarray): The array of minimum values (only if full_stats is True).
        - maxs (np.ndarray): The array of maximum values (only if full_stats is True).
    """
    # Remove NaN values across lat and lon dimensions for more robust stats
    valid_data = data.dropna(dim='lat', how='all').dropna(dim='lon', how='all')
    
    # Compute the median
    median = valid_data.median(dim=['lat', 'lon'], skipna=True)

    # Compute the values
    median_computed = median.compute()

    # Initialize the result dictionary with median
    result = {
        'times': median_computed['time'].values if 'time' in median_computed.dims else None,
        'medians': median_computed.values
    }

    # Compute additional statistics if full_stats is True
    if full_stats:
        mean = valid_data.mean(dim=['lat', 'lon'], skipna=True)
        q1 = valid_data.quantile(0.25, dim=['lat', 'lon'], skipna=True)
        q3 = valid_data.quantile(0.75, dim=['lat', 'lon'], skipna=True)
        min_val = valid_data.min(dim=['lat', 'lon'], skipna=True)
        max_val = valid_data.max(dim=['lat', 'lon'], skipna=True)

        mean_computed = mean.compute()
        q1_computed = q1.compute()
        q3_computed = q3.compute()
        min_computed = min_val.compute()
        max_computed = max_val.compute()

        # Update the result dictionary with additional statistics
        result.update({
            'means': mean_computed.values,
            'q1s': q1_computed.values,
            'q3s': q3_computed.values,
            'mins': min_computed.values,
            'maxs': max_computed.values
        })

    return result




def assign_color_spei(spei_values):
    """
    Assigns colors based on the Standardized Precipitation-Evapotranspiration Index (SPEI) values.
    This function takes a list of SPEI values and assigns a color code to each value based on the degree of wetness or dryness.
    The colors are assigned as follows:
    - Extremely wet: SPEI > 2.0 (color: '#006400')  # Dark Green
    - Severely wet: 1.5 < SPEI <= 2.0 (color: '#228B22')  # Forest Green
    - Moderately wet: 1.0 < SPEI <= 1.5 (color: '#32CD32')  # Lime Green
    - Near-normal / mildly wet: 0 < SPEI <= 1.0 (color: '#ADFF2F')  # Green Yellow
    - Near-normal / mildly dry: -1.0 < SPEI <= 0 (color: '#FFD700')  # Gold
    - Moderately dry: -1.5 < SPEI <= -1.0 (color: '#DAA520')  # Goldenrod
    - Severely dry: -2.0 < SPEI <= -1.5 (color: '#A0522D')  # Sienna
    - Extremely dry: SPEI <= -2.0 (color: '#8B4513')  # Saddle Brown
    If the SPEI value is NaN, the color will be transparent (color: 'rgba(0,0,0,0)').
    
    Parameters:
    spei_values (list of float): A list of SPEI values to be evaluated.

    Returns:
    list of str: A list of color codes corresponding to the SPEI values.
    
    Note: 
    neutral: #B89A7D - axes: #D3D3D3
    """
    colors = []
    for spei in spei_values:
        if math.isnan(spei):
            colors.append('rgba(0,0,0,0)')  # transparent for NaN values
        elif spei > 2.0:
            colors.append('#074B30')  # extremely wet
        elif 1.5 < spei <= 2.0:
            colors.append('#OD965f')  # severely wet
        elif 1.0 < spei <= 1.5:
            colors.append('#43EFAA')  # moderately wet
        elif 0 < spei <= 1.0:
            colors.append('#A1F7D5')  # near-normal / mildly wet
        elif -1.0 < spei <= 0:
            colors.append('#FFBF69')  # near-normal / mildly dry
        elif -1.5 < spei <= -1.0:
            colors.append('#FF961F')  # moderately dry
        elif -2.0 < spei <= -1.5:
            colors.append('#8F5100')  # severely dry
        elif spei <= -2.0:
            colors.append('#291700')  # extremely dry
    return colors


def create_scatterplot(values: dict, timescales: dict, selected: dict, placeholders: dict):
    """
    Creates and displays a scatterplot representing the SPEI over time, using provided data and user selections.
    It plots both mean (marked with dots) and median (marked with diamonds) SPEI values, each colored based on their respective values.

    Parameters:
    - values (dict): Contains time series data necessary for the plot, with keys 'times', 'means', and 'medians' that
                     list the years, mean SPEI values, and median SPEI values respectively.
    - timescales (dict): Maps timescale identifiers to their string representations, used for labeling in the plot.
    - selected (dict): User-selected filters for the plot, including 'timescale', 'country', 'area', and 'month'.
    """
    times = values['times']
    means = values['means']
    medians = values['medians']
    
    # Assign colors to means and medians based on their SPEI values
    mean_colors = assign_color_spei(means)
    median_colors = assign_color_spei(medians)
    
    # Prepare the text for the tooltips
    # Convert numpy.datetime64 for formatting
    mean_tooltip_texts = [f"{np.datetime64(time, 'D').astype('datetime64[M]').astype(object).strftime('%B %Y')}, mean: {mean:.2f}" for time, mean in zip(times, means)]
    median_tooltip_texts = [f"{np.datetime64(time, 'D').astype('datetime64[M]').astype(object).strftime('%B %Y')}, median: {median:.2f}" for time, median in zip(times, medians)]
        
    # Define the scatter plot for means
    mean_trace = go.Scatter(
        x=times,
        y=means,
        mode='markers',
        name='Mean SPEI',
        marker=dict(
            size=10,
            symbol='circle',
            color=mean_colors,
            line=dict(width=1, color='black')  # Border
        ),
        text=mean_tooltip_texts,  # Custom tooltip text
        hoverinfo='text'
    )
    
    # Define the scatter plot for medians
    median_trace = go.Scatter(
        x=times,
        y=medians,
        mode='markers',
        name='Median SPEI',
        marker=dict(
            size=10,
            symbol='diamond',
            color=median_colors,
            line=dict(width=1, color='black')  # Border
        ),
        text=median_tooltip_texts,  # Custom tooltip text
        hoverinfo='text'
    )
    
    timescale = selected['timescale']
    country = selected['country']
    _, area = get_adm_level_and_area_name(selected, placeholders)
    month = selected['month']
    
    # Initialize and update the figure
    fig = go.Figure([mean_trace, median_trace])
    fig.update_layout(
        title=f"{timescale} SPEI index, trends over time {area} in the month of {month}",
        xaxis_title='Year',
        yaxis_title=f"SPEI{timescales[timescale]} Value",
        height=600,
        template='plotly_white',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(
            zeroline=True,
            zerolinewidth=1,
            zerolinecolor='#D3D3D3'
        )
    )

    # Display the figure
    fig.show()




def create_boxplot(values: dict, timescales:dict, selected: dict, placeholders: dict):
    """
    Creates a boxplot chart using the provided boxplot statistics and colors the boxes based on SPEI index values.

    Parameters:
    values (dict): A dictionary containing 'times', 'medians', 'q1s', 'q3s', 'mins', 'maxs'.
    timescales (dict): A dictionary mapping timescale codes to their descriptions.
    selected (dict): A dictionary containing the 'timescale', 'country', 'area', and 'month'.
    spei_values (list of float): SPEI values corresponding to each time in `values['times']`.
    """
    times = values['times']
    medians = values['medians']
    q1s = values['q1s']
    q3s = values['q3s']
    mins = values['mins']
    maxs = values['maxs']
    
    times = pd.to_datetime(times).to_list()
    colors = assign_color_spei(medians)
    
    timescale = selected['timescale']
    country = selected['country']
    _, area = get_adm_level_and_area_name(selected, placeholders)
    month = selected['month']

    fig = go.Figure()

    for i, time in enumerate(times):
        fig.add_trace(go.Box(
            x=[time],  # Directly use datetime object for x-axis
            q1=[q1s[i]],  # Lower quartile (25th percentile)
            median=[medians[i]],  # Median
            q3=[q3s[i]],  # Upper quartile (75th percentile)
            lowerfence=[mins[i]],  # Minimum
            upperfence=[maxs[i]],  # Maximum
            name=str(time),  # Label with time value
            marker_color=colors[i],  # Color of the box based on SPEI
            whiskerwidth=0.2,  # Width of the whiskers
        ))

    fig.update_layout(
        title=f"{timescale} SPEI index, trends over time in {area} area in the month of {month}",
        xaxis_title='Years',
        yaxis_title=f"SPEI{timescales[timescale]}",
        height=600,
        template='plotly_white',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(
            zeroline=True,  # Ensure the zero line is visible
            zerolinewidth=1,
            zerolinecolor='#D3D3D3'  # Change zero line color to blue
        ),
        showlegend=False
    )

    fig.show()


    
    
def create_linechart(values: dict, timescales:dict, selected: dict, placeholders: dict):
    """
    Creates and displays a line chart with markers showing the Median SPEI trends over time based on the provided data and user selections. 
    This chart is specifically designed to depict how the SPEI changes over the months of a specific year within a selected region and area.

    Parameters:
    - values (dict): Contains time series data for the plot with keys:
        - 'times': A list of months or other time units.
        - 'medians': Corresponding medians SPEI values for each time unit.
        - 'colors': Colors for the markers; can be a single color or a list of colors that matches the length of 'times' and 'means'.
    - timescales (dict): Maps timescale identifiers to their string representations, which are used in the y-axis label of the chart.
    - selected (dict): Contains user-selected filters for the chart, including:
        - 'timescale': The SPEI timescale being displayed.
        - 'country': The country of interest.
        - 'area': The specific area within the country.
        - 'year': The year for which the data is plotted.
    """
    times = values['times']
    medians = values['medians']
    colors = assign_color_spei(medians)
    
    # Prepare the text for the tooltips
    # Convert numpy.datetime64 for formatting
    tooltip_texts = [f"{np.datetime64(time, 'D').astype('datetime64[M]').astype(object).strftime('%B %Y')}, median: {median:.2f}" for time, median in zip(times, medians)]

    # Define the line plot (trace) with markers
    trace = go.Scatter(
        x=times,
        y=medians,
        mode='lines+markers',  # Combine lines and markers
        name='Median SPEI',
        line=dict(
            color='#B89A7D',  # Define line color
            width=2           # Set line width
        ),
        marker=dict(
            color=colors,  # Colors for each marker
            size=15,        # Set marker size
            line = dict(
                color = "#B89A7D",
                width = 2
          )
        ),
        text=tooltip_texts,  # Custom tooltip text
        hoverinfo='text'
    )

    timescale = selected['timescale']
    country = selected['country']
    _, area = get_adm_level_and_area_name(selected, placeholders)
    year = selected['year']
    
    # Initialize and update the figure
    fig = go.Figure([trace])
    fig.update_layout(
        title=f"Median {timescale} SPEI index, trends over time in {area} area in {year}",
        xaxis_title='Months',
        yaxis_title=f"Median SPEI{timescales[timescale]}",
        height=600,
        template='plotly_white',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(
            zeroline=True,  # Ensure the zero line is visible
            zerolinewidth=1,
            zerolinecolor='#D3D3D3'  # Change zero line color
        )
    )

    # Display the figure
    fig.show()

    
    
def create_stripechart(values: dict, timescales: dict, selected: dict, placeholders: dict, aggregate_by: str = 'month'):
    """
    Generates generated chart is a vertical bar (stripe) chart, where each bar's color represents the median SPEI value for a specific period.

    Parameters:
        values (dict): A dictionary containing the data arrays for time points (`times`) and their corresponding median SPEI values (`medians`).
        timescales (dict): A dictionary that maps timescale identifiers to their SPEI calculation descriptions.
        selected (dict): A dictionary with selections for the timescale, country, area, and year range.
        start_year (int): The starting year for the visualization.
        end_year (int): The ending year for the visualization.
        aggregate_by (str): Determines the aggregation level of the data points in the visualization; default is 'month'. Other possible value is 'year'.
    """
    times = values['times']
    medians = values['medians']
    colors = assign_color_spei(medians)
    _, area = get_adm_level_and_area_name(selected, placeholders)
    
    # Convert numpy datetime64 to datetime64[M] for sorting
    date_transform = [np.datetime64(time, 'M') for time in times]

    # Pair date_transform, colors, and medians, then sort by date_transform
    paired_data = sorted(zip(date_transform, colors, medians), key=lambda x: x[0])
    sorted_dates = [date for date, _, _ in paired_data]
    sorted_colors = [color for _, color, _ in paired_data]
    sorted_medians = [median for _, _, median in paired_data]
    
    # Generate tooltip texts
    if aggregate_by == 'month':
        tooltip_texts = [f"{date.astype(object).strftime('%B %Y')}, median: {median:.2f}" for date, median in zip(sorted_dates, sorted_medians)]
        sorted_dates = [str(date) for date in sorted_dates]  # Convert to string for plotting
    else:
        tooltip_texts = [f"{date.astype(object).strftime('%B %Y')}, median: {median:.2f}" for date, median in zip(sorted_dates, sorted_medians)]
        sorted_dates = [date.astype('datetime64[Y]').astype(str)[:4] for date in sorted_dates]  # Show year on x-axis


    # Filter dates to show only specific years in ten-year intervals
    start_year = int(selected['year_range'][0])
    end_year = int(selected['year_range'][1])
    year_diff = end_year - start_year
    if year_diff <= 15:
        interval = (3, 1)
    elif year_diff > 15 and year_diff <= 25:
        interval = (5, 2)
    else:
        interval = (10, 10)
    if aggregate_by == 'month':
        target_years = [str(year) for year in range(start_year, end_year + 1, interval[0])]
        display_dates = [date[:4] if (date[:4] in target_years and date[5:7] == '01') else '' for date in sorted_dates]
    else:
        target_years = [str(year) for year in range(start_year, end_year + 1, interval[1])]
        display_dates = [year if year in target_years else '' for year in sorted_dates]

    # Create the stripe chart
    bar_width = 1.0 if aggregate_by == 'month' else 0.8
    fig = go.Figure(data=[
        go.Bar(
            x=sorted_dates,
            y=[1] * len(sorted_dates),
            marker_color=sorted_colors,
            hovertext=tooltip_texts,
            hoverinfo='text',
            orientation='v',
            width=bar_width
        )
    ])

    # Update layout
    fig.update_layout(
        title=f"Median {selected['timescale']} SPEI index, trends over time in {area} area from {selected['year_range'][0]} to {selected['year_range'][1]}",
        xaxis_title='Years',
        yaxis_title=f"Median SPEI{timescales[selected['timescale']]}",
        height=600,
        yaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
        xaxis={'type': 'category', 'tickmode': 'array', 'tickvals': sorted_dates, 'ticktext': display_dates, 'tickangle': 0},
        template='plotly_white',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
    )
    fig.update_yaxes(visible=False)
    fig.show()   
        
    
    

