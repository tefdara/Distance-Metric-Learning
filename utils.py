import os, json, asyncio

def deep_float_conversion(data):
    """
    Recursively convert string numbers to floats in a nested dict.
    Args:
        data: The data to convert.
    Returns:
        The converted float.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            data[key] = deep_float_conversion(value)
    elif isinstance(data, list):
        for index, value in enumerate(data):
            data[index] = deep_float_conversion(value)
    elif isinstance(data, str):
        try:
            # Check if the string can be converted to a float.
            return float(data)
        except ValueError:
            return data
    return data

def load_data(data_path):
    """
    Load the data from the data_path.
    Args:
        data_path: The path to the data directory.
    Returns:
        A list of dictionaries containing the data.
    """
    data_dicts = []
    if os.path.isdir(data_path):
        for root, dirs, files in os.walk(data_path):
            for file in files:
                if file.endswith(".json"):
                    try:
                        with open(os.path.join(root, file)) as json_file:
                            data_content = json.load(json_file)
                            
                            # Convert any string numbers to floats in the nested dict.
                            data_dicts.append(deep_float_conversion(data_content))
                    except json.JSONDecodeError:
                        print(f"Error decoding JSON from file: {file}")
                    except Exception as e:
                        print(f"Error reading from file {file}. Error: {e}")
    else:
       raise ValueError("The data path must be a directory.")
    return data_dicts

import shutil

async def copy_similar_to_folders(base_path, data_path, file_id, similar_files):
    """
    Copy files of similar sounds to separate folders.
    Args:
        base_path: The base path to store the folders.
        data_path: The path to the data directory.
        file_id: The ID of the file to copy.
        similar_files: A list of IDs of similar files.
    Returns:
        None
    """
    if(len(similar_files) == 0):
        return
    # Create a directory for the sound_id
    target_folder = os.path.join(base_path, file_id)
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
    
    # create a directory for the analysis files
    analysis_folder = os.path.join(target_folder, "analysis")
    if not os.path.exists(analysis_folder):
        os.makedirs(analysis_folder)
        
    # This assumes that the source directory is one level above the data_path
    source_diectory = os.path.dirname(data_path)
    
    sound_files = similar_files + [file_id]
    for sound in sound_files:
        # Assuming each sound has an associated JSON file
        source_file_path = os.path.join(source_diectory, sound)
        source_file_without_extension = os.path.splitext(sound)[0]
        # also copy the analysis files
        analysis_file = source_file_without_extension+"_analysis.json"
        analysis_file_path = os.path.join(data_path, analysis_file)
        # Copy the file to the target directory
        if os.path.exists(source_file_path):
            # check if the file already exists in the target directory
            if not os.path.exists(os.path.join(target_folder, sound)):
                print(f"Copying {source_file_without_extension} to {target_folder}")
                shutil.copy2(source_file_path, target_folder)
            if not os.path.exists(os.path.join(analysis_folder, analysis_file)):
                print(f"Copying {analysis_file_path} to {analysis_folder}")
                shutil.copy2(analysis_file_path, analysis_folder)
        else:
            print(f"File {source_file_path} not found!")

        await asyncio.sleep(1)  # just to mimic some delay
    print(f"Copied similar sounds for {file_id} to {target_folder}.")
    
    
def group_by_criteria(df, criteria_col):
    """
    Group sounds by a specific column/criteria.
    Args:
        df: DataFrame containing the data.
        criteria_col: The column by which to group the sounds.
    Returns:
        A list of lists containing the sounds grouped by the criteria.
    """
    return [list(group["id"]) for _, group in df.groupby(criteria_col)]

def shorten_key(key):
    """
    Shorten a key by removing the first part of the key.
    Args:
        key: The key to shorten.
    Returns:
        The shortened key.
    """
    if(key is None):
        return None
    if('lowlevel' in key):
        key = key.split('lowlevel_')[-1]
    if('metadata' in key):
        key = key.split('metadata_')[-1]
    if('rhythm' in key):
        key = key.split('rhythm_')[-1]
    if('tonal' in key):
        key = key.split('tonal_')[-1]
        
    return key

def shorten_key(key): 
    return key.split('lowlevel_')[-1] if 'lowlevel' in key\
                                        else key.split('metadata_')[-1] if 'metadata' in key\
                                        else key.split('rhythm_')[-1] if 'rhythm' in key\
                                        else key.split('tonal_')[-1] if 'tonal' in key\
                                        else key.split('audio_properties_')[-1] if 'audio_properties' in key\
                                        else key if key is not None else None
                                        
def flatten_dict(d, parent_key='', sep='_'):
    items = {}
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        new_key = shorten_key(new_key)
        
        if isinstance(v, dict):
            items.update(flatten_dict(v, new_key, sep=sep))
        # If the value is a list, flatten with indexed keys
        elif isinstance(v, list):
            for idx, item in enumerate(v):
                stat_type = new_key.split('_')[-1]
                key_without_stat = new_key.split('_' + stat_type)[0]
                indexed_key = f"{key_without_stat}_{idx}_{stat_type}"
                # # Add the index to the key without an underscore separator
                # indexed_key = f"{new_key}{idx}"
                items[indexed_key] = item
        else:
            items[new_key] = v
    return items

def flatten_structure(data):
     return flatten_dict(data)          
     



