import netCDF4 as nc
import math
import numpy as np
import pandas as pd
import json
import time
from datetime import datetime
import plotly.graph_objects as go
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
        
    
    

