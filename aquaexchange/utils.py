import os
import json
import geopandas as gpd

def ensure_directory_exists(directory):
    """
    Ensures the given directory exists, creating it if necessary.
    
    Parameters:
    - directory (str): Path of the directory to check or create.
    """
    os.makedirs(directory, exist_ok=True)

def save_json(data, filepath):
    """
    Saves a dictionary as a JSON file.
    
    Parameters:
    - data (dict): The data to save.
    - filepath (str): Path to the output JSON file.
    """
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)

def load_json(filepath):
    """
    Loads a JSON file and returns its contents as a dictionary.
    
    Parameters:
    - filepath (str): Path to the input JSON file.
    
    Returns:
    - dict: Parsed JSON data.
    """
    with open(filepath, "r") as f:
        return json.load(f)

def clean_intermediate_files(directory, keep_extensions=(".json", ".tif", ".aux.xml")):
    """
    Deletes all intermediate files from a directory except those with specified extensions.

    Parameters:
    - directory (str): Path to the directory to clean.
    - keep_extensions (tuple): File extensions to keep (default: JSON, TIF, and XML).
    """
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path) and not filename.endswith(keep_extensions):
            os.remove(file_path)

def load_geojson(filepath):
    """
    Loads a GeoJSON file into a GeoDataFrame.
    
    Parameters:
    - filepath (str): Path to the GeoJSON file.
    
    Returns:
    - GeoDataFrame: Geospatial data.
    """
    return gpd.read_file(filepath)

def save_geojson(gdf, filepath):
    """
    Saves a GeoDataFrame as a GeoJSON file.

    Parameters:
    - gdf (GeoDataFrame): The geospatial data to save.
    - filepath (str): Path to the output GeoJSON file.
    """
    gdf.to_file(filepath, driver="GeoJSON")
