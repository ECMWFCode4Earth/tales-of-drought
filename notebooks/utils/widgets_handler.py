import netCDF4 as nc
import pandas as pd
import json
import os
import time



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


            

def month_year_interaction(btn_name, month_selector, year_selector, selected, placeholders):
    """
    Handle interactions between the month and year selectors, resetting the other selector
    when one is changed, or resetting both if year_range is explicitly changed.

    Args:
    change (dict): The change event dictionary containing the owner and new value of the change.
    month_selector (object): The selector object for months.
    year_selector (object): The selector object for years.
    selected (dict): A dictionary storing the currently selected month and year.
    placeholders (dict): A dictionary containing placeholder texts for the selectors.
    """
    if btn_name == 'month_widgets_btn':
        year_selector.value = placeholders['year']
        selected['year'] = placeholders['year']
    elif btn_name == 'year_widgets_btn':
        month_selector.value = placeholders['month']
        selected['month'] = placeholders['month']
    elif btn_name == 'year_range_widgets_btn':
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
