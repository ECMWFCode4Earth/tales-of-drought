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
import hvplot.xarray
from utils.widgets_handler import read_json_to_dict
from utils.widgets_handler import get_adm_level_and_area_name

color_palette_json = 'color_palette_bright.json'

def assign_colors(values):
    """
    Assigns colors based on the input values.
    This function takes a dictionary of values and assigns a color code to each value based on the degree of wetness or dryness.
    If the value is NaN, the color will be transparent (color: 'rgba(0,0,0,0)').

    Parameters:
    cmap (dict of float): A dictionary of colors from the json file.

    Returns:
    list of str: A list of color codes corresponding to the values.
    
    Note: 
    neutral: #B89A7D - axes: #D3D3D3
    """
    # Load the categories and colors from the JSON file
    cmap = read_json_to_dict(color_palette_json)
    
    colors = []
    for val in values:
        if math.isnan(val):
            colors.append('rgba(0,0,0,0)')  # transparent for NaN values
        elif val > 2.0:
            colors.append(cmap["Extremely wet"])
        elif 1.5 < val <= 2.0:
            colors.append(cmap["Severely wet"])
        elif 1.0 < val <= 1.5:
            colors.append(cmap["Moderately wet"])
        elif 0 < val <= 1.0:
            colors.append(cmap["Mildly wet"])
        elif -1.0 < val <= 0:
            colors.append(cmap["Mildly dry"])
        elif -1.5 < val <= -1.0:
            colors.append(cmap["Moderately dry"])
        elif -2.0 < val <= -1.5:
            colors.append(cmap["Severely dry"])
        elif val <= -2.0:
            colors.append(cmap["Extremely dry"])
    return colors



def plot_geographical_distribution(ds):
    """
    Plots a geographical map showing the distribution of SPEI (Standardized Precipitation-Evapotranspiration Index) values
    at a specified time index from a dataset. The function utilizes a Plate Carree projection to display the data 
    on a 2D map, color-coded according to SPEI values using a brown-green color map. The map includes coastlines for better geographical context.
    It automatically extracts the SPEI values for the specified time, formats the date for the title, 
    and plots the data on the map. The color bar is added to indicate the range and intensity of SPEI values, enhancing interpretability.

    Parameters:
        data (xarray.DataArray or xarray.Dataset): The dataset to plot.
        groupby (str): The variable to group by for creating an animation.
        clim (tuple): The color limits for the plot.
        widget_type (str): The type of widget to use for the plot.
        widget_location (str): The location of the widget.
        projection (cartopy.crs.Projection): The projection to use for the plot.
        coastline (str): The resolution of the coastline to plot.
        cmap (str): The colormap to use for the plot.
        features (list): Additional features to add to the plot (e.g., borders).
        width (int): The width of the plot in pixels.
        height (int): The height of the plot in pixels.
    
    Returns:
        hvplot object: The plot to be rendered.
    """
    
    plot = ds.hvplot(
        groupby='time',
        clim=(-2, 2),
        widget_type="scrubber", 
        widget_location="bottom", 
        projection=ccrs.PlateCarree(), 
        coastline='10m',
        cmap='BrBG',
        features=['borders'],
        width=800,
        height=600
    )
    return plot



def create_scatterplot(values: dict, accumulation_windows: dict, selected: dict, placeholders: dict):
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
    - accumulation_windows (dict): Maps accumulation_window identifiers (e.g., 'monthly', 'annual') to their descriptive
                         names, which are used for labeling in the plot.
    - selected (dict): Specifies the filters applied to the data, including:
        - 'accumulation_window': The selected accumulation_window identifier.
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
    cmap = read_json_to_dict(color_palette_json)
    mean_colors = assign_colors(means)
    median_colors = assign_colors(medians)
    
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
    for category, color in cmap.items():
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode='markers',
            marker=dict(size=10, color=color),
            name=category,
            legendgroup='colors', showlegend=True,
            hoverinfo='none'
    ))
    
    accumulation_window = selected['accumulation_window']
    country = selected['country']
    _, area = get_adm_level_and_area_name(selected, placeholders)
    month = selected['month']
    
    # Update the figure
    fig.update_layout(
        title=f"{accumulation_window} SPEI index, trends over time {area} in the month of {month}",
        xaxis_title='Years',
        yaxis_title=f"SPEI{accumulation_windows[accumulation_window]} Value",
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




def create_boxplot(values: dict, accumulation_windows: dict, selected: dict, placeholders: dict):
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
    - accumulation_windows (dict): A dictionary mapping accumulation_window codes to their descriptive names.
    - selected (dict): A dictionary containing selected parameters for the plot:
        - 'accumulation_window': The code of the accumulation_window to use.
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
    cmap = read_json_to_dict(color_palette_json)
    colors = assign_colors(medians)
    
    accumulation_window = selected['accumulation_window']
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
    for category, color in cmap.items():
        fig.add_trace(go.Box(
            x=[None], y=[None],
            name=category,
            marker_color=color,
            legendgroup='colors', 
            showlegend=True,  # Ensure only these are shown in the legend
            hoverinfo='none'
        ))

    fig.update_layout(
        title=f"{accumulation_window} SPEI index, trends over time in {area} in the month of {month}",
        xaxis_title='Years',
        yaxis_title=f"SPEI{accumulation_windows[accumulation_window]} Value",
        height=600,
        template='plotly_white',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(zeroline=True, zerolinewidth=1, zerolinecolor='#D3D3D3'),
        legend_title="SPEI Categories",
        showlegend=True
    )

    fig.show()

    
    
def create_linechart(values: dict, accumulation_windows: dict, selected: dict, placeholders: dict):
    """
    Creates and displays a line chart with markers to depict Median SPEI (Standardized Precipitation-Evapotranspiration Index) trends 
    over the months of a selected year within a specified region and area. Each point on the line chart is color-coded based on its 
    SPEI value to provide visual cues about drought conditions.

    Parameters:
    - values (dict): Contains time series data for the plot, including:
        - 'times': List of datetime objects representing the months.
        - 'medians': List of median SPEI values corresponding to each time point.
    - accumulation_windows (dict): Maps accumulation_window identifiers (e.g., 'monthly', 'annual') to their descriptive
                         names, used for axis labeling and titles.
    - selected (dict): Specifies the filters and selections for the plot:
        - 'accumulation_window': The selected accumulation_window identifier.
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
    cmap = read_json_to_dict(color_palette_json)
    colors = assign_colors(medians)
    
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

    accumulation_window = selected['accumulation_window']
    country = selected['country']
    _, area = get_adm_level_and_area_name(selected, placeholders)
    year = selected['year']
    
    fig = go.Figure([trace])

    # Add dummy traces for color legend
    for category, color in cmap.items():
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
        title=f"Median {accumulation_window} SPEI index, trends over time in {area} in {year}",
        xaxis_title='Months',
        yaxis_title=f"Median SPEI{accumulation_windows[accumulation_window]}",
        height=600,
        template='plotly_white',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(zeroline=True, zerolinewidth=1, zerolinecolor='#D3D3D3'),
        legend_title="SPEI Categories"
    )

    fig.show()

    
    
def create_stripechart(values: dict, accumulation_windows: dict, selected: dict, placeholders: dict, aggregate_by: str = 'month'):
    """
    Generates a vertical bar (stripe) chart that visualizes the median SPEI (Standardized Precipitation-Evapotranspiration Index) values over a specified time period. 
    Each bar represents a specific period (month or year based on aggregation) and is color-coded based on the median SPEI value, facilitating an intuitive understanding 
    of drought severity over time. The chart features tooltips that provide detailed information about the median SPEI for each period when hovered over. 

    Parameters:
        values (dict): Contains the time points (`times`) and their corresponding median SPEI values (`medians`).
        accumulation_windows (dict): Maps accumulation_window identifiers to their SPEI calculation descriptions, used for labeling the chart.
        selected (dict): Stores user-selected filters including:
            - 'accumulation_window': The SPEI accumulation_window (e.g., monthly, annual).
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
    cmap = read_json_to_dict(color_palette_json)
    colors = assign_colors(medians)
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
    for category, color in cmap.items():
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
        title=f"Median {selected['accumulation_window']} SPEI index, trends over time in {area} area from {selected['year_range'][0]} to {selected['year_range'][1]}",
        xaxis_title='Years',
        yaxis_title=f"Median SPEI{accumulation_windows[selected['accumulation_window']]}",
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



    
    
def create_combined_areachart(stat_values: dict, selected: dict, placeholders: dict):
    """
    Creates a combined area chart for multiple time series data, each representing a different accumulation window.

    This function iterates over a dictionary of statistical values (medians), where each key represents a specific 
    accumulation window (e.g., "1 month", "3 months", ...) and its associated data. It plots these accumulation windows
    as area charts on a single figure, with each accumulation window differentiated by a unique color. 
    The function also configures tooltip texts for better data visualization, showing detailed information on hover.

    Parameters:
    - stat_values (dict): A dictionary where each key is a accumulation window descriptor (e.g., "1 month") and 
      each value is another dictionary containing 'times' and 'medians' which are lists of times (datetime) 
      and corresponding median values respectively.
    - selected (dict): A dictionary containing selection parameters such as the accumulation window and 
      country. This information is used to customize the chart's title and other textual content.
    - placeholders (dict): A dictionary used to handle dynamic placeholders in the widget system.

    The charts are displayed using Plotly library, with each area chart's fill extending down to the zero y-axis. 
    The colors are predefined in a list and are cycled through for each timescale if more than seven timescales are present.

    Returns:
    None: The function directly displays the figure using `fig.show()`.
    """
    
    # List of 7 distinct colors for the 7 different accumulation windows
    colors = ['#4D24AC', '#F73A91', '#29DAE4', '#5570EF', '#8021BE', '#ffafcc', '#cdb4db']
    start_year, end_year = map(int, selected['twenty_years'].split('-'))

    
    fig = go.Figure()  # Initialize the figure outside the loop
    
    for i, (timescale, values) in enumerate(stat_values.items()):
        times = values['times']
        medians = values['medians']

        tooltip_texts = [
            f"{np.datetime64(time, 'D').astype('datetime64[M]').astype(object).strftime('%B %Y')}, median: {median:.2f}"
            for time, median in zip(times, medians)
        ]

        # Ensure there is a color for each timescale or cycle through colors
        color = colors[i % len(colors)]

        # Create a trace for each timescale
        trace = go.Scatter(
            x=times,
            y=medians,
            mode='lines+markers',
            name=f'Median SPEI {timescale}',
            line=dict(color=color, width=2),
            marker=dict(color=color, size=2),
            text=tooltip_texts,
            hoverinfo='text',
            fill='tozeroy'  # Fills the area under the line
        )
        
        fig.add_trace(trace)  # Add the trace to the figure

    accumulation_window = selected['accumulation_window']
    country = selected['country']
    _, area = get_adm_level_and_area_name(selected, placeholders)

    # Update the layout once, not in the loop
    fig.update_layout(
        title=f"Median SPEI indices, trends over time in {area} from {start_year} to {end_year}",
        xaxis_title='Years',
        yaxis_title='Median SPEI',
        height=600,
        template='plotly_white',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(zeroline=True, zerolinewidth=1, zerolinecolor='#D3D3D3'),
        legend_title="SPEI Categories",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    fig.show()
