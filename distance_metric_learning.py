#!/usr/bin/env python3.9

import asyncio, argparse, yaml, sys
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from scipy.spatial import distance
from utils import *


def find_n_most_similar(identifier, df, metric=None, n=5, clss="stats"):
    """
    Find the indices of the n most similar files based on all metrics or a specific metric.
    Args:
        identifier: The ID of the file to compare.
        df: The DataFrame containing the data.
        metric: The metric to use for comparison.
        n: The number of similar files to retrieve.
        clss: The class to use for comparison, i.e., keys to nested dictionaries containing the metrics.
    Returns:
        A list of indices of the n most similar sounds.
    """
    # Standardize either specific metric or all metrics under a class
    descriptors_columns = [col for col in df.columns if clss in col]
    
    if metric:
        metric = clss + "_" + metric
        if metric not in df.columns:
            raise ValueError(f"The metric {metric} doesn't exist in the data.")
        scaler = StandardScaler()
        df[metric + "_standardized"] = scaler.fit_transform(df[[metric]])
        columns_to_compare = [metric + "_standardized"]
    else:
        scaler = StandardScaler()
        standardized_features = scaler.fit_transform(df[descriptors_columns])
        df[descriptors_columns] = standardized_features
        columns_to_compare = descriptors_columns
    
    sound_data = df[df["id"] == identifier].iloc[0]
    distances = []
    for index, row in df.iterrows():
        if row["id"] != identifier:
            dist = distance.euclidean(sound_data[columns_to_compare].values, row[columns_to_compare].values)
            distances.append((row["id"], dist))
    
    distances.sort(key=lambda x: x[1])
    return [item[0] for item in distances[:n]]

def find_n_most_similar_weighted(identifier, df, ops):
    """
    Find the indices of the n most similar files based on all metrics or a specific metric.
    Args:
        identifier: The ID of the file to compare.
        df: The DataFrame containing the data.
        metric: The metric to use for comparison.
        n: The number of similar files to retrieve.
        clss: The class to use for comparison.
        ops: The options file containing the weights for each metric.
    Returns:
        A list of indices of the n most similar sounds.
    """
    clss = ops["class"]
    n = ops["n"]
    # Extract and standardize the metrics
    data_columns = [col for col in df.columns if clss in col]
    scaler = StandardScaler()
    standardized_features = scaler.fit_transform(df[data_columns])
    df[data_columns] = standardized_features
    columns_to_compare = data_columns

    # Set default weights
    weights = {col: 1 for col in data_columns}

    if 'weights' in ops:
        if ops['exclusive_weights'] is True:
            weights = {}  # Reset weights
        for key, value in ops['weights'].items():
            col_name = clss + "_" + key
            if col_name in data_columns:
                weights[col_name] = value

    # Compute weighted Euclidean distance
    sound_data = df[df["id"] == identifier].iloc[0]
    if sound_data.isnull().values.any():
        raise ValueError("Invalid sound data")
    distances = []

    for index, row in df.iterrows():
        if row["id"] != identifier:
            weighted_diffs = [(sound_data[col] - row[col]) * weights.get(col, 1) for col in data_columns]
            dist = np.sqrt(sum(diff ** 2 for diff in weighted_diffs))
            distances.append((row["id"], dist))
    
    distances.sort(key=lambda x: x[1])
    print(distances)
    return [item[0] for item in distances[:n]]


def find_n_most_similar_classifications(identifier, df, classification_category=None, n=5, clss="classifications"):
    """Find the indices of the n most similar files based on classifications."""
    
    if classification_category:
        # Extract specific classification columns
        columns_to_compare = [col for col in df.columns if clss in col and classification_category in col]
    else:
        # Extract all classification columns
        columns_to_compare = [col for col in df.columns if clss in col]
    
    sound_data = df[df["id"] == identifier]
    distances = []
    for index, row in df.iterrows():
        if row["id"] != identifier:
            dist = distance.euclidean(sound_data[columns_to_compare].values[0], row[columns_to_compare].values)
            distances.append((row["id"], dist))
    
    distances.sort(key=lambda x: x[1])
    return [item[0] for item in distances[:n]]

def find_n_most_similar_for_a_file(used_files, id, df, metric=None, n=10, clss="stats", ops=None):
    """
    Find n most similar files for the given file which aren't in used_files.
    """
    df_copy = df.copy()
    df_copy = df_copy[~df_copy['id'].isin(used_files)]  # Exclude already used files before finding similar ones
    
    if(clss == "classifications"):
        return find_n_most_similar_classifications(id, df_copy, n=n, clss=clss)
    if ops:
        find_n_most_similar_weighted(id, df_copy, ops)
    else:
        return find_n_most_similar(id, df_copy, metric=metric, n=n, clss=clss)
        
async def process_batch(all_files, used_files, df, metric=None, n=5, clss="stats", id=None, ops=None):
    """Process a batch of sounds asynchronously."""
    if(id):
        primary_file = id
    else:
        primary_file = all_files.pop()
    similar_files = find_n_most_similar_for_a_file(used_files=used_files, id=primary_file, df=df, metric=metric, n=n, clss=clss, ops=ops)
    print(f"Found {len(similar_files)} similar files for {primary_file}.")
    await copy_similar_to_folders(base_path, data_path, primary_file, similar_files)
    used_files.update(similar_files)
    all_files.difference_update(used_files)
    

if(__name__ == "__main__"):
    
    parser = argparse.ArgumentParser(description='Process some arguments.')
    parser.add_argument('-d', '--data-path', type=str, required=True,
                        help='Path to the data directory')
    parser.add_argument('-id', '--identifier', type=str,
                        help='Identifier to test')
    parser.add_argument('-bp', '--base-path', type=str, default='./similar_files',
                        help='Base directory to store all similar file groups')
    parser.add_argument('-cls', '--class_to_analyse', type=str, default='stats',
                        help='Class to analyse')
    parser.add_argument('-m', '--metric-to-analyze', type=str, default=None,
                        help='Metric to analyze')
    parser.add_argument('-n', type=int, default=5,
                        help='Number of similar sounds to retrieve')
    parser.add_argument('-ops', action='store_true', default=False,
                        help='Use opetions file to fine tune the metric learning')
    parser.add_argument('-nm', '--n-max', type=int, default=-1, 
                        help='Max number of similar files to retrieve, Default: -1 (all)')

    args = parser.parse_args()
    data_path = os.path.abspath(args.data_path)
    identifier_to_test = args.identifier
    base_path = args.base_path
    class_to_analyse = args.class_to_analyse
    metric_to_analyze = args.metric_to_analyze
    n = args.n
    use_options_file = args.ops
    ops = None
    n_max = args.n_max
    
    if(use_options_file):
        # Load the options yamle file from this directory
        ops_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "metric_ops.yaml")
        ops = yaml.load(open(ops_file), Loader=yaml.FullLoader)
        
    
    # Load the data
    data = load_data(data_path)
    # Convert to DataFrame
    df = pd.json_normalize(data, sep="_")
    
    all_files = set(df["id"].tolist())
    if n_max == -1:
        n_max = len(all_files)
    used_files = set()
    loop = asyncio.get_event_loop()
    
    while all_files and len(used_files) < n_max:
        loop.run_until_complete(process_batch(all_files=all_files, used_files=used_files, df=df, metric=metric_to_analyze, n=n, clss=class_to_analyse, id=identifier_to_test, ops=ops))
    


    
    
    
    
