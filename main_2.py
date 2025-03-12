import json
import os
import geopandas as gpd
from merge_geojson import merge_geojson
from satellite_imagery_processor import process_satellite_imagery

def main():
    # Define input GeoJSON file
    input_geojson = "C:/Users/rivur/Documents/SS_GLX/AquaExchange/Output_geojson_test/FM12715.geojson"
    merged_output_folder = "merged_geojsons"

    os.makedirs(merged_output_folder, exist_ok=True)

 # Merge the input GeoJSON
    merged_geojson_path = merge_geojson(input_geojson, merged_output_folder)


    output_dir = "C:/Users/rivur/Documents/SS_GLX/AquaExchange/output"
    os.makedirs(output_dir, exist_ok=True)

    # Process satellite imagery for the merged GeoJSON
    farm_id = os.path.splitext(os.path.basename(merged_geojson_path))[0]
    print(f"Processing satellite imagery for {farm_id}...")

    result = process_satellite_imagery(merged_geojson_path, output_dir=output_dir)

    # Save the final output JSON
    output_json_path = "output_main_2.json"
    with open(output_json_path, "w") as f:
        json.dump(result, f, indent=4)

    print(f"Processing complete. Images saved in '{output_dir}' and JSON output saved to '{output_json_path}'.")

if __name__ == "__main__":
    main()
