import netCDF4 as nc
import xarray as xr
import dask
import numpy as np
import pandas as pd
import glob
import os
import time
from datetime import datetime
import cftime
from IPython.display import display
from utils.coordinates_retrieve import generate_coordinate_values


    
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



def generate_file_patterns(btn_name, selectors, placeholders, months, selected_accumulation_window, middle_pattern, data_path):
    """
    Generate file patterns to match NetCDF files based on the selected criteria.

    Parameters:
    btn_name (str): Button name to determine the type of data fetching.
    selectors (dict): Dictionary containing widget selectors.
    placeholders (dict): Placeholder values for widgets.
    months (dict): Dictionary of month abbreviations to numbers.
    selected_accumulation_window (str): The selected accumulation_window.
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
                file_pattern = f'SPEI{selected_accumulation_window}{middle_pattern}{year}{month}*.nc'
                file_patterns.extend(glob.glob(os.path.join(data_path, file_pattern)))
    elif btn_name == 'accumulation_windows_widgets_btn':
        start_year, end_year = map(int, selectors['twenty_years'].value.split('-'))
        file_patterns = []
        for year in range(int(start_year), int(end_year) + 1):
            for month in months.values():
                file_pattern = f'SPEI{selected_accumulation_window}{middle_pattern}{year}{month}*.nc'
                file_patterns.extend(glob.glob(os.path.join(data_path, file_pattern)))
    else:
        selected_month = months[selectors['month'].value] if selectors['month'].value != placeholders['month'] else None
        selected_year = selectors['year'].value if selectors['year'].value != placeholders['year'] else None
        file_pattern = f'SPEI{selected_accumulation_window}{middle_pattern}'
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
    bounds (tuple): Geographic boundary coordinates (min_lon, min_lat, max_lon, max_lat).

    Returns:
    xarray.Dataset: The processed dataset.
    """
    return xr.open_mfdataset(
        valid_files,
        concat_dim='time',
        combine='nested',
        parallel=False,   # If kernel returns an error set parallel to False
        preprocess=lambda ds: preprocess(ds, bounds)
    )


def get_xarray_data(btn_name, bounds, selectors, placeholders, months, accumulation_windows):
    """
    Load and process a dataset of climate data for a specified month, year, and geographic area.

    Parameters:
    bounds (tuple): Geographic boundary coordinates (min_lon, min_lat, max_lon, max_lat).
    btn_name (str): Button name to determine the type of data fetching.
    selectors (dict): Dictionary containing widget selectors.
    placeholders (dict): Placeholder values for widgets.
    months (dict): Dictionary of month abbreviations to numbers.
    accumulation_windows (dict): Dictionary of available accumulation_windows.

    Returns:
    xarray.Dataset or None: The processed dataset or None if no readable files are found.
    """
    selected_accumulation_window = accumulation_windows[selectors['accumulation_window'].value]
    data_path = f'/data1/drought_dataset/spei/spei{selected_accumulation_window}/'
    middle_pattern = '*global_era5*_moda_ref1991to2020_'
    
    file_patterns = generate_file_patterns(btn_name, selectors, placeholders, months, selected_accumulation_window, middle_pattern, data_path)
    
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


    
    
def display_data_details(btn_name, selected, subset):
    """
    Displays details of the selected data and subset based on the specified index.

    Parameters:
    selected (dict): A dictionary containing selection attributes such as country, subarea, month, year, and accumulation_window.
    subset (list of xr.DataArray): A list of xarray DataArrays containing the subset data.

    Returns:
    None: This function only prints details to the console.
    """
    print("Country: ", selected['country'])
    print("ADM1 subarea: ", selected['adm1_subarea'])
    print("ADM2 subarea: ", selected['adm2_subarea'])
    if btn_name == 'month_widgets_btn':
        print("Month: ", selected['month'])
    elif btn_name == 'year_widgets_btn':
        print("Year: ", selected['year'])
    elif  btn_name == 'year_range_widgets_btn':
        print("Year range: ", selected['year_range'])
    elif  btn_name == 'accumulation_windows_widgets_btn':
        print("Year range: ", selected['twenty_years'])
    print("accumulation_window: ", selected['accumulation_window'], '\n')

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
        'invalid_ratio': round((invalid_ratio * 100), 2),
        'duplicates_removed': duplicate_removed_count,
        'cftime_conversions': conversion_count
    }



def compute_stats(data: xr.DataArray, full_stats: bool = True) -> dict:
    """
    Computes the basic statistics from the SPEI data over latitude and longitude.
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
    # Chunk the data along latitude and longitude to spped up the calculation
    data = data.chunk({'lat': 'auto', 'lon': 'auto'})
    
    # Remove NaN values across lat and lon dimensions for more robust stats
    valid_data = data.dropna(dim='lat', how='all').dropna(dim='lon', how='all')
    
    # Initialize the result dictionary
    result = {}

    # Compute the median and mean together to avoid recomputation
    median = valid_data.median(dim=['lat', 'lon'], skipna=True)
    mean = valid_data.mean(dim=['lat', 'lon'], skipna=True)

    # Compute additional statistics if full_stats is True
    if full_stats:
        q1 = valid_data.quantile(0.25, dim=['lat', 'lon'], skipna=True)
        q3 = valid_data.quantile(0.75, dim=['lat', 'lon'], skipna=True)
        min_val = valid_data.min(dim=['lat', 'lon'], skipna=True)
        max_val = valid_data.max(dim=['lat', 'lon'], skipna=True)
        
        # Compute all stats at once, parallelized
        median_computed, mean_computed, q1_computed, q3_computed, min_computed, max_computed = dask.compute(
            median, mean, q1, q3, min_val, max_val
        )
        
        result.update({
            'means': mean_computed.values,
            'q1s': q1_computed.values,
            'q3s': q3_computed.values,
            'mins': min_computed.values,
            'maxs': max_computed.values,
        })
    else:
        median_computed, mean_computed = dask.compute(median, mean)

    # Update the result dictionary with median and time values
    result.update({
        'times': median_computed['time'].values if 'time' in median_computed.dims else None,
        'medians': median_computed.values,
    })

    return result

