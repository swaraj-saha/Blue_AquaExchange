import json
import os
import geopandas as gpd
import pandas as pd
from aquaexchange.buffer import buffer_ponds
from aquaexchange.search_stac_images import search_stac_images
from aquaexchange.calculate_indices import process_nwi
from aquaexchange.find_previous_lulc import assign_previous_lulc_class

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

def process_initial_data(farm_json):
    """
    Processes farm data and saves the JSON output in data/.
    """
    farm_id = farm_json.get("farmid", "Unknown")
    
    # (Processing steps remain unchanged...)

    final_output = {
        "farmid": farm_id,
        "noofponds": len(gdf),
        "ponds": []
    }

    for _, row in merged_df.iterrows():
        final_output["ponds"].append({
            "id": row["pond_id"],
            "Probable Year of Change": row.get("nwi_first_year", "no data"),
            "Previous Class": row.get("lulc_class", "no data"),
            "Present Class": "Pond"
        })

    # ✅ Save JSON output inside data/
    output_path = os.path.join(DATA_DIR, "output_main_1.json")
    with open(output_path, "w") as f:
        json.dump(final_output, f, indent=4)

    print(f"Saved processed JSON to {output_path}")
    return final_output
