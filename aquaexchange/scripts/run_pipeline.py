import json
import os
import shutil
from scripts.main_1 import process_initial_data
from scripts.main_2 import process_farm_data
from aquaexchange.combine_outputs import combine_results

DATA_DIR = "data"

def cleanup_intermediate_files():
    """
    Deletes intermediate GeoJSON and temporary files while keeping input JSON,
    final output JSON, and essential files (.tif, .xml).
    """
    for root, dirs, files in os.walk(DATA_DIR, topdown=False):
        for file in files:
            if not (file.endswith(".json") or file.endswith(".tif") or file.endswith(".xml")):
                os.remove(os.path.join(root, file))
        for dir in dirs:
            if dir in ["geojsons", "merged_geojsons", "images"]:
                shutil.rmtree(os.path.join(root, dir), ignore_errors=True)

def run_pipeline(farm_json_path):
    """
    Executes the full processing pipeline for a given farm JSON input.
    
    Parameters:
    - farm_json_path (str): Path to the input farm JSON file.
    
    Returns:
    - None
    """
    # Load the input JSON
    with open(farm_json_path, "r") as f:
        farm_json = json.load(f)

    # Step 1: Process initial data (buffering, Landsat search, NWI, LULC)
    initial_results = process_initial_data(farm_json)

    # Save intermediate structured output
    initial_output_path = os.path.join(DATA_DIR, "initial_output.json")
    with open(initial_output_path, "w") as f:
        json.dump(initial_results, f, indent=4)

    # Step 2: Process farm data (GeoJSON conversion, merging, satellite processing)
    satellite_results = process_farm_data(farm_json)

    # Save another intermediate structured output
    satellite_output_path = os.path.join(DATA_DIR, "satellite_output.json")
    with open(satellite_output_path, "w") as f:
        json.dump(satellite_results, f, indent=4)

    # Step 3: Combine results into a final output JSON
    final_results = combine_results(initial_results, satellite_results)

    final_output_path = os.path.join(DATA_DIR, "final_output.json")
    with open(final_output_path, "w") as f:
        json.dump(final_results, f, indent=4)

    # Cleanup intermediate files
    cleanup_intermediate_files()

    print(f"Pipeline completed. Final output saved at: {final_output_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python run_pipeline.py <path_to_farm_json>")
    else:
        run_pipeline(sys.argv[1])
