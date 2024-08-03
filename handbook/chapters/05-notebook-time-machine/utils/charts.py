import netCDF4 as nc
import math
import numpy as np
import pandas as pd
import json
import time
from datetime import datetime
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from utils.widgets_handler import read_json_to_dict
from utils.widgets_handler import get_adm_level_and_area_name


def assign_color_spei(spei_values):
    """
    Assigns colors based on the Standardized Precipitation-Evapotranspiration Index (SPEI) values.
    This function takes a dictionary of SPEI values and assigns a color code to each value based on the degree of wetness or dryness.
    The colors are assigned as follows:
    - Extremely wet: SPEI > 2.0 (color: '#074B30')
    - Severely wet: 1.5 < SPEI <= 2.0 (color: '#0D965f')
    - Moderately wet: 1.0 < SPEI <= 1.5 (color: '#43EFAA')
    - Near-normal / mildly wet: 0 < SPEI <= 1.0 (color: '#A1F7D5')
    - Near-normal / mildly dry: -1.0 < SPEI <= 0 (color: '#FFBF69')
    - Moderately dry: -1.5 < SPEI <= -1.0 (color: '#FF961F')
    - Severely dry: -2.0 < SPEI <= -1.5 (color: '#8F5100')
    - Extremely dry: SPEI <= -2.0 (color: '#291700')
    If the SPEI value is NaN, the color will be transparent (color: 'rgba(0,0,0,0)').

    Parameters:
    spei_categories (dict of float): A dictionary of SPEI values from the spei_categories.json file.

    Returns:
    list of str: A list of color codes corresponding to the SPEI values.
    
    Note: 
    neutral: #B89A7D - axes: #D3D3D3
    """
    # Load the categories and colors from the JSON file
    spei_categories = read_json_to_dict('spei_categories.json')
    
    colors = []
    for spei in spei_values:
        if math.isnan(spei):
            colors.append('rgba(0,0,0,0)')  # transparent for NaN values
        elif spei > 2.0:
            colors.append(spei_categories["Extremely wet"])
        elif 1.5 < spei <= 2.0:
            colors.append(spei_categories["Severely wet"])
        elif 1.0 < spei <= 1.5:
            colors.append(spei_categories["Moderately wet"])
        elif 0 < spei <= 1.0:
            colors.append(spei_categories["Mildly wet"])
        elif -1.0 < spei <= 0:
            colors.append(spei_categories["Mildly dry"])
        elif -1.5 < spei <= -1.0:
            colors.append(spei_categories["Moderately dry"])
        elif -2.0 < spei <= -1.5:
            colors.append(spei_categories["Severely dry"])
        elif spei <= -2.0:
            colors.append(spei_categories["Extremely dry"])
    return colors



def plot_spei_geographical_distribution(ds, time_index):
    """
    Plots a geographical map showing the distribution of SPEI (Standardized Precipitation-Evapotranspiration Index) values
    at a specified time index from a dataset. The function utilizes a Plate Carree projection to display the data 
    on a 2D map, color-coded according to SPEI values using a brown-green color map. The map includes coastlines for better geographical context.
    It automatically extracts the SPEI values for the specified time, formats the date for the title, 
    and plots the data on the map. The color bar is added to indicate the range and intensity of SPEI values, enhancing interpretability.

    Parameters:
        time_index (int): The index of the time slice in the dataset to visualize. This index corresponds to a specific time point 
                          in the dataset's time dimension.

    Returns:
        None: Displays the map using matplotlib's plt.show() function without returning any objects. 
    """
    fig, ax = plt.subplots(figsize=(12, 8), subplot_kw={'projection': ccrs.PlateCarree()})
    
    # Select the data at the given time index
    spei_values = ds.isel(time=time_index)
    
    # Format the datetime object to show only the date in yyyy-mm-dd format
    formatted_date = np.datetime_as_string(spei_values.time.values, unit='D')
    
    # Plot data
    pcolormesh = spei_values.plot.pcolormesh(ax=ax, transform=ccrs.PlateCarree(), 
                                             add_colorbar=True, cmap='BrBG')
    
    ax.set_title(f"{formatted_date}")
    ax.coastlines()
    plt.show()



def create_scatterplot(values: dict, timescales: dict, selected: dict, placeholders: dict):
    """
    Creates and displays a scatterplot of the Standardized Precipitation-Evapotranspiration Index (SPEI)
    over time, using provided data points for both mean and median values. The plot marks mean values
    with dots and median values with diamonds, each colored according to their SPEI categories. Tooltips
    provide additional data insights on hover.

    Parameters:
    - values (dict): Contains time series data for the plot, including:
        - 'times': List of datetime objects representing the years.
        - 'means': List of mean SPEI values corresponding to the times.
        - 'medians': List of median SPEI values corresponding to the times.
    - timescales (dict): Maps timescale identifiers (e.g., 'monthly', 'annual') to their descriptive
                         names, which are used for labeling in the plot.
    - selected (dict): Specifies the filters applied to the data, including:
        - 'timescale': The selected timescale identifier.
        - 'country': The country for the data.
        - 'area': Specific area within the country.
        - 'month': The month for which the data is visualized.
    - placeholders (dict): A dictionary containing placeholder values for additional
                           configuration, such as ADM level and area names.

    Returns:
    - None: This function creates and displays the scatterplot directly using the Plotly visualization library.
    """
    times = values['times']
    means = values['means']
    medians = values['medians']
    
    
    # Assign colors to means and medians based on their SPEI values
    spei_categories = read_json_to_dict('spei_categories.json')
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
    
    
    # Initialize and update the figure
    fig = go.Figure([mean_trace, median_trace])
    
    # Add dummy traces for color legend using the spei categories
    for category, color in spei_categories.items():
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode='markers',
            marker=dict(size=10, color=color),
            name=category,
            legendgroup='colors', showlegend=True,
            hoverinfo='none'
    ))
    
    timescale = selected['timescale']
    country = selected['country']
    _, area = get_adm_level_and_area_name(selected, placeholders)
    month = selected['month']
    
    # Update the figure
    fig.update_layout(
        title=f"{timescale} SPEI index, trends over time {area} in the month of {month}",
        xaxis_title='Years',
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




def create_boxplot(values: dict, timescales: dict, selected: dict, placeholders: dict):
    """
    Creates a boxplot chart using the provided boxplot statistics, where boxes are colored 
    based on SPEI index values. This function also configures the plot with custom labels 
    and a legend that indicates different SPEI categories.

    Parameters:
    - values (dict): A dictionary containing key statistics for the boxplot:
        - 'times': List of times (dates).
        - 'medians': List of median values.
        - 'q1s': List of first quartile values.
        - 'q3s': List of third quartile values.
        - 'mins': List of minimum values.
        - 'maxs': List of maximum values.
    - timescales (dict): A dictionary mapping timescale codes to their descriptive names.
    - selected (dict): A dictionary containing selected parameters for the plot:
        - 'timescale': The code of the timescale to use.
        - 'country': The country for which the data is plotted.
        - 'area': The area within the country.
        - 'month': The month for which the data is plotted.
    - placeholders (dict): A dictionary containing placeholder values for additional 
      configuration, such as ADM level and area names.

    Returns:
    - None: This function directly displays the boxplot using Plotly's visualization library.
    """
    times = values['times']
    medians = values['medians']
    q1s = values['q1s']
    q3s = values['q3s']
    mins = values['mins']
    maxs = values['maxs']
    
    times = pd.to_datetime(times).to_list()
    spei_categories = read_json_to_dict('spei_categories.json')
    colors = assign_color_spei(medians)
    
    timescale = selected['timescale']
    country = selected['country']
    _, area = get_adm_level_and_area_name(selected, placeholders)
    month = selected['month']

    fig = go.Figure()

    # Create box traces with showlegend set to False
    for i, time in enumerate(times):
        fig.add_trace(go.Box(
            x=[time],
            q1=[q1s[i]],
            median=[medians[i]],
            q3=[q3s[i]],
            lowerfence=[mins[i]],
            upperfence=[maxs[i]],
            name=str(time),  # This is used for hovertext but not for the legend
            marker_color=colors[i],
            whiskerwidth=0.2,
            showlegend=False  # Disable showing each box in the legend
        ))

    # Add dummy traces for color legend
    for category, color in spei_categories.items():
        fig.add_trace(go.Box(
            x=[None], y=[None],
            name=category,
            marker_color=color,
            legendgroup='colors', 
            showlegend=True,  # Ensure only these are shown in the legend
            hoverinfo='none'
        ))

    fig.update_layout(
        title=f"{timescale} SPEI index, trends over time in {area} in the month of {month}",
        xaxis_title='Years',
        yaxis_title=f"SPEI{timescales[timescale]} Value",
        height=600,
        template='plotly_white',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(zeroline=True, zerolinewidth=1, zerolinecolor='#D3D3D3'),
        legend_title="SPEI Categories",
        showlegend=True
    )

    fig.show()

    
    
    
def create_std_dev_bar_chart(values: dict, timescales: dict, selected: dict, placeholders: dict):
    """
    Generates a bar chart that displays the mean Standardized Precipitation-Evapotranspiration Index (SPEI) values 
    across different years for a specific month and location. The bars are colored based on the SPEI categories and 
    include error bars representing the standard deviation of the SPEI values.

    Parameters:
        values (dict): A dictionary containing the datasets needed for plotting. It includes:
            - 'times': A list of time points (typically years).
            - 'means': A list of mean SPEI values corresponding to each time point.
            - 'std_devs': A list of standard deviations for the SPEI values at each time point.
        timescales (dict): A dictionary mapping timescale codes to their descriptions, used for labeling.
        selected (dict): A dictionary specifying the selections made for visualization:
            - 'timescale': The timescale code (e.g., 'monthly', 'annual').
            - 'country': The country of interest.
            - 'area': The specific area within the country.
            - 'month': The month for which the data is plotted.
        placeholders (dict): A dictionary containing additional placeholder values used in the function,
                             like administrative level and area names.

    Returns:
        None: The function creates and displays the bar chart directly using Plotly's visualization capabilities.
    """
    spei_categories = widgets_handler.read_json_to_dict('spei_categories.json')
    
    times = pd.to_datetime(values['times'])
    means = values['means']
    std_devs = values['std_devs']
    
    mean_colors = charts.assign_color_spei(means)

    timescale = selected['timescale']
    country = selected['country']
    _, area = widgets_handler.get_adm_level_and_area_name(selected, placeholders)
    month = selected['month']

    # Create the bar chart
    fig = go.Figure()

    # Main bar trace
    fig.add_trace(go.Bar(
        x=times,
        y=means,
        error_y=dict(
            type='data',  # Standard deviation
            array=std_devs,
            visible=True
        ),
        marker_color=mean_colors,
        name='Monthly SPEI'
    ))

    # This trace will not show in the legend
    fig.data[0].showlegend = False

    # Add dummy bars for the SPEI color categories legend
    for category, color in spei_categories.items():
        fig.add_trace(go.Bar(
            x=[None],  # Dummy data point, not visible in the chart
            y=[None],
            marker_color=color,
            name=category,
            showlegend=True  # This ensures it shows in the legend
        ))

    # Update plot layout
    fig.update_layout(
        title=f"Mean {timescale} SPEI and standard deviation for the month of {month} across years in {area}",
        xaxis_title='Years',
        yaxis_title=f"SPEI {timescales[timescale]}",
        height=600,
        template='plotly_white',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(
            zeroline=True,
            zerolinewidth=1,
            zerolinecolor='#D3D3D3'
        ),
        legend_title="SPEI Categories"
    )

    # Display the figure
    fig.show()

    
    
def create_linechart(values: dict, timescales: dict, selected: dict, placeholders: dict):
    """
    Creates and displays a line chart with markers to depict Median SPEI (Standardized Precipitation-Evapotranspiration Index) trends 
    over the months of a selected year within a specified region and area. Each point on the line chart is color-coded based on its 
    SPEI value to provide visual cues about drought conditions.

    Parameters:
    - values (dict): Contains time series data for the plot, including:
        - 'times': List of datetime objects representing the months.
        - 'medians': List of median SPEI values corresponding to each time point.
    - timescales (dict): Maps timescale identifiers (e.g., 'monthly', 'annual') to their descriptive
                         names, used for axis labeling and titles.
    - selected (dict): Specifies the filters and selections for the plot:
        - 'timescale': The selected timescale identifier.
        - 'country': The country for which the data is plotted.
        - 'area': Specific area within the country.
        - 'year': The year for which the data is visualized.
    - placeholders (dict): Contains placeholder values and additional configuration data,
                           such as administrative level and area names, which are used in labeling and tooltips.

    Returns:
    - None: The function directly displays the line chart using the Plotly visualization library.

    The line chart includes a custom tooltip for each data point that shows the month and year along with the median SPEI value, enhancing 
    user interaction by providing detailed context. Additionally, a legend for SPEI categories is included to assist with interpretation of the SPEI values.
    """
    times = values['times']
    medians = values['medians']
    spei_categories = read_json_to_dict('spei_categories.json')
    colors = assign_color_spei(medians)
    
    tooltip_texts = [
        f"{np.datetime64(time, 'D').astype('datetime64[M]').astype(object).strftime('%B %Y')}, median: {median:.2f}"
        for time, median in zip(times, medians)
    ]

    trace = go.Scatter(
        x=times,
        y=medians,
        mode='lines+markers',
        name='Median SPEI',
        line=dict(color='#B89A7D', width=2),
        marker=dict(color=colors, size=15, line=dict(color="#B89A7D", width=2)),
        text=tooltip_texts,
        hoverinfo='text',
        showlegend=False  # Do not show this trace in the legend
    )

    timescale = selected['timescale']
    country = selected['country']
    _, area = get_adm_level_and_area_name(selected, placeholders)
    year = selected['year']
    
    fig = go.Figure([trace])

    # Add dummy traces for color legend
    for category, color in spei_categories.items():
        fig.add_trace(go.Scatter(
            x=[None], y=[None],
            mode='markers',  # Only markers needed for the legend
            marker=dict(color=color, size=10),
            name=category,
            legendgroup='colors',
            showlegend=True,
            hoverinfo='none'
        ))

    fig.update_layout(
        title=f"Median {timescale} SPEI index, trends over time in {area} in {year}",
        xaxis_title='Months',
        yaxis_title=f"Median SPEI{timescales[timescale]}",
        height=600,
        template='plotly_white',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(zeroline=True, zerolinewidth=1, zerolinecolor='#D3D3D3'),
        legend_title="SPEI Categories"
    )

    fig.show()

    
    
def create_stripechart(values: dict, timescales: dict, selected: dict, placeholders: dict, aggregate_by: str = 'month'):
    """
    Generates a vertical bar (stripe) chart that visualizes the median SPEI (Standardized Precipitation-Evapotranspiration Index) values over a specified time period. 
    Each bar represents a specific period (month or year based on aggregation) and is color-coded based on the median SPEI value, facilitating an intuitive understanding 
    of drought severity over time. The chart features tooltips that provide detailed information about the median SPEI for each period when hovered over. 

    Parameters:
        values (dict): Contains the time points (`times`) and their corresponding median SPEI values (`medians`).
        timescales (dict): Maps timescale identifiers to their SPEI calculation descriptions, used for labeling the chart.
        selected (dict): Stores user-selected filters including:
            - 'timescale': The SPEI timescale (e.g., monthly, annual).
            - 'country': The country for the data.
            - 'area': Specific area within the country.
            - 'year_range': Tuple of (start_year, end_year) defining the range for visualization.
        placeholders (dict): Holds placeholder data and additional configuration items for display purposes.
        aggregate_by (str): Determines the aggregation level for data points (default 'month'). 
                            'year' is the other possible value, allowing for annual aggregation.

    Returns:
        None: The function directly creates and displays the stripe chart using Plotly's visualization capabilities.
    """
    times = values['times']
    medians = values['medians']
    spei_categories = read_json_to_dict('spei_categories.json')
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
    fig = go.Figure()
    
    
    fig.add_trace(go.Bar(
        x=sorted_dates,
        y=[1] * len(sorted_dates),
        marker_color=sorted_colors,
        hovertext=tooltip_texts,
        hoverinfo='text',
        orientation='v',
        showlegend=False,  # Disable showing each bar in the legend
        width=bar_width
    ))
    
        # Add dummy bars for color legend
    for category, color in spei_categories.items():
        fig.add_trace(go.Bar(
            x=[None],
            y=[None],
            marker_color=color,
            name=category,
            showlegend=True,  # Enable legend only for dummy bars
            hoverinfo='none'
    ))
        

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
        showlegend=True,
        legend_title="SPEI Categories"
    )
    fig.update_yaxes(visible=False)
    fig.show()   
        
    
    

