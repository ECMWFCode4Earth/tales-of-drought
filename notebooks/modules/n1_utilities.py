import netCDF4 as nc
import xarray as xr
import dask
import numpy as np
import pandas as pd
import glob
import os
import cftime
import folium
from IPython.display import display, IFrame
import plotly.graph_objects as go
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import time
from datetime import datetime
import json


def save_selection(selection):
    """
    Save the current selection to a JSON file.

    Parameters:
    selection (dict): A dictionary containing the current selections of country, subarea, month, year, and timescale.
    """
    # Construct the file path relative to the current script's directory
    current_dir = os.path.dirname(__file__)
    file_path = os.path.join(current_dir, '..', 'data', 'previous_selection.json')
    with open(file_path, 'w') as file:
        json.dump(selection, file)
        


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
    
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        if sort:
            sorted_data = {country: sorted(subareas) for country, subareas in sorted(data.items())}
            return sorted_data    
        return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {}






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
    # Ensure only existing coordinates are used for subsetting
    latitude_list = [lat for lat in latitude_list if lat in ds.lat.values]
    longitude_list = [lon for lon in longitude_list if lon in ds.lon.values]
    if not latitude_list or not longitude_list:
        raise ValueError("Generated coordinates do not match any available in the dataset.")    
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



def get_bounds(area):
    """
    Retrieve the bounding box coordinates for a given country.

    Parameters:
    area (str): The name of the country or its subarea for which to retrieve the bounding box.

    Returns:
    tuple or str: A tuple containing the bounding box coordinates in the format 
                  (min_lat, max_lat, min_lon, max_lon) if successful, 
                  or an error message if not.
    """
    geolocator = Nominatim(user_agent="talesofdrought")     # Initialize the Nominatim client
    try:
        # Use geocode to query the country with the parameter for getting bounding box
        location = geolocator.geocode(area, exactly_one=True, timeout=10)
        if location:
            # Extract the bounding box
            bounding_box = location.raw['boundingbox']
            bounds = (float(bounding_box[0]), float(bounding_box[1]),
                      float(bounding_box[2]), float(bounding_box[3]))
            return bounds
        else:
            return "No data found."
    except GeocoderTimedOut:
        print(f"Geocoding timed out for {area}; retrying...")
        time.sleep(1)
        return get_bounds(country)  # Retry for this area
    except Exception as e:
        return f"Error retrieving data for {area}: {e}"
    

    
    
def update_subarea_selector(change, placeholder_country, placeholder_subarea, subarea_selector, country_to_subareas):
    """
    Update the options of a subarea selector widget based on the selected country from thr related selector widget.

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


          
           
def handle_area_change(bounds, selected_month, selected_year, selected_timescale):
    """
    Load and process a dataset of climate data for a specified month, year, and geographic area.

    Parameters:
    bounds (tuple): Geographic boundary coordinates.
    selected_month (str or None): Month for which data is to be loaded, in two-digit format (e.g., "01").
    selected_year (str or None): Year for which data is to be loaded, in four-digit format (e.g., "1990").
    selected_timescale (str): Timescale for the SPEI index.

    Returns:
    xarray.Dataset or None: The processed dataset or None if no readable files are found.
    """
    data_path = f'/data1/drought_dataset/spei/spei{selected_timescale}/'
    # Flexible pattern to match both 'era5' and 'era5t'
    middle_pattern = '*global_era5*_moda_ref1991to2020_'
    file_pattern = f'SPEI{selected_timescale}{middle_pattern}'
    file_pattern += f'{selected_year if selected_year else "????"}{selected_month if selected_month else "??"}*.nc'
    try:
        file_list = sorted(glob.glob(os.path.join(data_path, file_pattern)))
        valid_files = [file for file in file_list if is_readable_nc(file)]
        if not valid_files:
            print("No readable NetCDF files found.")
            return None

        data = xr.open_mfdataset(
            valid_files,
            concat_dim='time',
            combine='nested',
            parallel=True,
            preprocess=lambda ds: preprocess(ds, bounds)  # Ensure preprocess function is defined to handle bounds
        )
        return data
    except Exception as e:
        print(f"An error occurred: {e}")
        return None




def update_display(country_selector, subarea_selector, month_selector, year_selector, timescale_selector, months, timescales, placeholders):
    """
    Updates the area subset data based on user selections from the dropdown widgets. The function dynamically 
    adjusts the displayed data depending on the selected country, subarea, month, year, and timescale. 

    Parameters:
    - country_selector (Widget): Widget for selecting a country.
    - subarea_selector (Widget): Widget for selecting a subarea within a country.
    - month_selector (Widget): Widget for selecting a month.
    - year_selector (Widget): Widget for selecting a year.
    - timescale_selector (Widget): Widget for selecting a timescale for data aggregation.
    - months (dict): Dictionary mapping month names to their respective numerical representations.
    - timescales (dict): Dictionary mapping timescale identifiers to their descriptive strings.
    - placeholders (dict): Dictionary containing placeholder values used as defaults in the selectors to handle cases where no selection is made.

    The function checks for valid selections and retrieves corresponding bounds based on the geographical selections.
    It then fetches or recalculates the data for the specified area, time frame, and timescale, updating the global 
    `area_subset_data` accordingly.

    If valid data is available based on the selections, it outputs the updated data scope. If selections are incomplete 
    or data is unavailable, it provides feedback via printed messages.

    Returns:
    - Returns the updated `area_subset_data` if the selections are complete and valid data is available, 
      otherwise returns None.
    """
    global area_subset_data
    bounds = get_bounds(subarea_selector.value if subarea_selector.value != placeholders['subarea'] else country_selector.value)
    selected_month = months.get(month_selector.value) if month_selector.value != placeholders['month'] else None
    selected_year = year_selector.value if year_selector.value != placeholders['year'] else None
    selected_timescale = timescales.get(timescale_selector.value, placeholders['timescale'])
        
    if bounds and (selected_month or selected_year) and selected_timescale != placeholders['timescale']:
        area_subset_data = handle_area_change(bounds, selected_month, selected_year, selected_timescale)
        if area_subset_data and selected_month:
            print(f"Data updated for: Area={bounds}, Month={selected_month}, Timescale={selected_timescale}")
        elif area_subset_data and selected_year:
            print(f"Data updated for: Area={bounds}, Year={selected_year}, Timescale={selected_timescale}")
        else:
            print("No data available for the selected area, month/year, and timescale")
        return area_subset_data
    else:
        print("Selection incomplete. Please select all required options.")



def replace_invalid_values(data: pd.DataFrame, invalid_value: float = -9999.0) -> pd.DataFrame:
    """
    Replaces invalid values in the dataset with NaN.

    Parameters:
    data (pd.DataFrame): The DataFrame to process.
    invalid_value (float): The value to replace with NaN. Default is -9999.0.

    Returns:
    pd.DataFrame: The DataFrame with invalid values replaced by NaN.
    """
    return data.where(data != invalid_value, np.nan)



def compute_means(data: xr.DataArray) -> dict:
    """
    Computes the mean SPEI over latitude and longitude,
    and extracts the times and values for plotting. Also assigns colors based on the SPEI values.

    Parameters:
    data (xr.DataArray): The DataArray containing the SPEI data with dimensions including 'lat', 'lon', and 'time'.

    Returns:
    dict: A dict containing:
        - times (np.ndarray): The array of time values.
        - values (np.ndarray): The array of mean SPEI values over the specified dimensions.
        - colors (np.ndarray): The array of colors assigned based on the SPEI values.
    """
    mean_spei = data.mean(dim=['lat', 'lon'])
    mean_spei_computed = mean_spei.compute()
    
    # Extract times and values for plotting
    times = mean_spei_computed['time'].values
    means = mean_spei_computed.values
    colors = assign_color_spei(means)
    
    return {
        'times': times,
        'means': means,
        'colors': colors,
    }


def create_scatterplot(values: dict, timescales: dict, selected: dict):
    """
    Creates and displays a scatterplot representing the mean SPEI over time, using provided data and user selections.

    Parameters:
    - values (dict): Contains time series data necessary for the plot, with keys 'times', 'means', and 'colors' that
                     list the years, mean SPEI values, and colors for each data point, respectively.
    - timescales (dict): Maps timescale identifiers to their string representations, used for labeling in the plot.
    - selected (dict): User-selected filters for the plot, including 'timescale', 'country', 'subarea', and 'month'.
    """
    times = values['times']
    means = values['means']
    colors = values['colors']
    
    # Define the scatter plot (trace)
    trace = go.Scatter(
        x=times,
        y=means,
        mode='markers',
        name=f"Mean SPEI",
        marker=dict(
            size=10,
            color=colors,
            line=dict(width=0, color='#717BFA')
        )
    )
    
    timescale = selected['timescale']
    country = selected['country']
    subarea = selected['subarea']
    month = selected['month']
    
    # Initialize and update the figure
    fig = go.Figure([trace])
    fig.update_layout(
        title=f"Mean {timescale} SPEI Index, trends over time in {country}'s {subarea} area for the month of {month}",
        xaxis_title='Years',
        yaxis_title=f"Mean SPEI{timescales[timescale]}",
        height=500,
        plot_bgcolor='white',   # Sets the plotting area background color
        paper_bgcolor='white',  # Sets the overall background color of the chart
        xaxis=dict(
            showgrid=True,  # Enable grid (default)
            gridcolor='#D3D3D3',  # Set grid color
            linecolor='#D3D3D3',  # Set axis line color
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#D3D3D3',
            linecolor='#D3D3D3',
            zeroline=True,  # Ensure the zero line is visible
            zerolinewidth=1,
            zerolinecolor='black'  # Change zero line color to blue
        )
    )

    # Display the figure
    fig.show()



def compute_boxplot_stats(data: xr.DataArray) -> dict:
    """
    Computes the statistics needed to create a boxplot from the SPEI data over latitude and longitude.
    These statistics include the median, lower and upper quantiles (25th and 75th percentiles), minimum, and maximum values.

    Parameters:
    data (xr.DataArray): The DataArray containing the SPEI data with dimensions including 'lat', 'lon', and 'time'.

    Returns:
    dict: A dictionary containing:
        - times (np.ndarray): The array of time values.
        - medians (np.ndarray): The array of median values over the specified dimensions.
        - q1s (np.ndarray): The array of 25th percentile values.
        - q3s (np.ndarray): The array of 75th percentile values.
        - mins (np.ndarray): The array of minimum values.
        - maxs (np.ndarray): The array of maximum values.
    """
    # Compute the required statistics
    median = data.median(dim=['lat', 'lon'])
    q1 = data.quantile(0.25, dim=['lat', 'lon'])
    q3 = data.quantile(0.75, dim=['lat', 'lon'])
    min_val = data.min(dim=['lat', 'lon'])
    max_val = data.max(dim=['lat', 'lon'])

    # Compute the values
    median_computed = median.compute()
    q1_computed = q1.compute()
    q3_computed = q3.compute()
    min_computed = min_val.compute()
    max_computed = max_val.compute()

    # Extract times and values
    times = median_computed['time'].values
    medians = median_computed.values
    q1s = q1_computed.values
    q3s = q3_computed.values
    mins = min_computed.values
    maxs = max_computed.values

    return {
        'times': times,
        'medians': medians,
        'q1s': q1s,
        'q3s': q3s,
        'mins': mins,
        'maxs': maxs
    }



def create_boxplot(values: dict, timescales, selected):
    """
    Creates a boxplot chart using the provided boxplot statistics and colors the boxes based on SPEI index values.

    Parameters:
    values (dict): A dictionary containing 'times', 'medians', 'q1s', 'q3s', 'mins', 'maxs'.
    timescales (dict): A dictionary mapping timescale codes to their descriptions.
    selected (dict): A dictionary containing the 'timescale', 'country', 'subarea', and 'month'.
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
    subarea = selected['subarea']
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
        title=f"Boxplot of {timescale} SPEI Index, trends over time in {country}'s {subarea} area for the month of {month}",
        xaxis_title='Years',
        yaxis_title=f"SPEI{timescales[timescale]}",
        height=500,
        plot_bgcolor='white',   # Sets the plotting area background color
        paper_bgcolor='white',  # Sets the overall background color of the chart
        xaxis=dict(
            showgrid=True,  # Enable grid (default)
            gridcolor='#D3D3D3',  # Set grid color
            linecolor='#D3D3D3',  # Set axis line color
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#D3D3D3',
            linecolor='#D3D3D3',
            zeroline=True,  # Ensure the zero line is visible
            zerolinewidth=1,
            zerolinecolor='black'  # Change zero line color to blue
        ),
        showlegend=False
    )

    fig.show()


    
    
def create_linechart(values: dict, timescales: dict, selected: dict):
    """
    Creates and displays a line chart with markers showing the Mean SPEI trends over time based on the provided data and user selections. 
    This chart is specifically designed to depict how the SPEI changes over the months of a specific year within a selected region and subarea.

    Parameters:
    - values (dict): Contains time series data for the plot with keys:
        - 'times': A list of months or other time units.
        - 'means': Corresponding mean SPEI values for each time unit.
        - 'colors': Colors for the markers; can be a single color or a list of colors that matches the length of 'times' and 'means'.
    - timescales (dict): Maps timescale identifiers to their string representations, which are used in the y-axis label of the chart.
    - selected (dict): Contains user-selected filters for the chart, including:
        - 'timescale': The SPEI timescale being displayed.
        - 'country': The country of interest.
        - 'subarea': The specific subarea within the country.
        - 'year': The year for which the data is plotted.
    """
    times = values['times']
    means = values['means']
    colors = values['colors']  # This should be a single color or a list of colors matching the length of times and means

    # Define the line plot (trace) with markers
    trace = go.Scatter(
        x=times,
        y=means,
        mode='lines+markers',  # Combine lines and markers
        name='Mean SPEI',
        line=dict(
            color='#B89A7D',  # Define line color
            width=2           # Set line width
        ),
        marker=dict(
            color=colors,  # Colors for each marker
            size=20,        # Set marker size
        )
    )

    timescale = selected['timescale']
    country = selected['country']
    subarea = selected['subarea']
    year = selected['year']
    
    # Initialize and update the figure
    fig = go.Figure([trace])
    fig.update_layout(
        title=f"Mean {timescale} SPEI Index, trends over time in {country}'s {subarea} area in {year}",
        xaxis_title='Months',
        yaxis_title=f"Mean SPEI{timescales[timescale]}",
        height=500,
        plot_bgcolor='white',   # Sets the plotting area background color
        paper_bgcolor='white',  # Sets the overall background color of the chart
        xaxis=dict(
            showgrid=True,  # Enable grid (default)
            gridcolor='#D3D3D3',  # Set grid color
            linecolor='#D3D3D3',  # Set axis line color
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#D3D3D3',
            linecolor='#D3D3D3',
            zeroline=True,  # Ensure the zero line is visible
            zerolinewidth=1,
            zerolinecolor='black'  # Change zero line color
        )
    )

    # Display the figure
    fig.show()

    
    
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
    
    Note: 
    neutral: #B89A7D - axes: #D3D3D3
    """
    colors = []
    for spei in spei_values:
        if spei > 2.0:
            colors.append('#064A78')  # extremely wet
        elif 1.5 < spei <= 2.0:
            colors.append('#3c8fc3')  # severely wet
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
