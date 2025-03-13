import json
import os
from aquaexchange.geojson_maker import create_geojson
from aquaexchange.merge_geojson import merge_geojson
from aquaexchange.satellite_imagery_processor import process_satellite_imagery
from aquaexchange.image_uploader import upload_bytes_to_azure, generate_sas_url

DATA_DIR = "data"
GEOJSON_DIR = os.path.join(DATA_DIR, "geojsons")
MERGED_DIR = os.path.join(DATA_DIR, "merged_geojsons")

def process_farm_data(farm_json):
    print("Processing farm data...")

    os.makedirs(GEOJSON_DIR, exist_ok=True)
    os.makedirs(MERGED_DIR, exist_ok=True)

    create_geojson(farm_json, output_dir=GEOJSON_DIR)
    farm_id = farm_json["farmid"]
    input_geojson = os.path.join(GEOJSON_DIR, f"{farm_id}.geojson")

    merged_geojson_path = merge_geojson(input_geojson, MERGED_DIR)

    print(f"Processing satellite imagery for {farm_id}...")
    image_dict = process_satellite_imagery(merged_geojson_path)

    azure_urls = []
    for filename, image_bytes in image_dict.items():
        blob_name = upload_bytes_to_azure("opensource-product", filename, image_bytes)
        if blob_name:
            azure_urls.append(generate_sas_url("opensource-product", blob_name))

    output = {"images": azure_urls}
    
    with open(os.path.join(DATA_DIR, "output_main_2.json"), "w") as f:
        json.dump(output, f, indent=4)

    print("Saved processed JSON to output_main_2.json")
    return output
