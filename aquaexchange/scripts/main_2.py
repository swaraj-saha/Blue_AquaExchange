import json
import os
import shutil
from aquaexchange.geojson_maker import create_geojson
from aquaexchange.merge_geojson import merge_geojson
from aquaexchange.satellite_processor import process_satellite_imagery

DATA_DIR = "data"
GEOJSON_DIR = os.path.join(DATA_DIR, "geojsons")
MERGED_DIR = os.path.join(DATA_DIR, "merged_geojsons")
IMAGES_DIR = os.path.join(DATA_DIR, "images")

def process_farm_data(farm_json):
    """
    Processes farm data and saves the JSON output in data/.
    """
    print("Processing farm data...")

    # Ensure required directories exist
    os.makedirs(GEOJSON_DIR, exist_ok=True)
    os.makedirs(MERGED_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)

    # Convert JSON to GeoJSON
    create_geojson(farm_json, output_dir=GEOJSON_DIR)

    # Get the farm ID (assuming one farm per request)
    farm_id = farm_json["farmid"]
    input_geojson = os.path.join(GEOJSON_DIR, f"{farm_id}.geojson")

    # Merge GeoJSONs
    merged_geojson_path = merge_geojson(input_geojson, MERGED_DIR)

    # Process satellite imagery
    print(f"Processing satellite imagery for {farm_id}...")
    result = process_satellite_imagery(merged_geojson_path, output_dir=IMAGES_DIR)

    # ✅ Save JSON output inside data/
    output_path = os.path.join(DATA_DIR, "output_main_2.json")
    with open(output_path, "w") as f:
        json.dump(result, f, indent=4)

    print(f"Saved processed JSON to {output_path}")
    return result
