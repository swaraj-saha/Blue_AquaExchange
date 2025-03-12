import json
import geopandas as gpd
import pandas as pd
from buffer import buffer_ponds
from search_stack_images import search_stac_images
from calculate_indices import process_nwi
from find_previous_lulc import assign_previous_lulc_class
from find_previous_lulc import parse_lulc_labels  # New XML parsing function

# Define input/output paths
PONDS_GEOJSON = "C:/Users/rivur/Documents/SS_GLX/AquaExchange/Output_geojson_test/FM18207.geojson"
BUFFERED_GEOJSON = "test/output/buffered_ponds.geojson"
FINAL_OUTPUT_JSON = "test/output/final_output.json"
LULC_XML_FILE = "C:/Users/rivur/Documents/SS_GLX/AquaExchange/LULC_AP/drive-download-20250312T040019Z-001/lulc_with_labels_1999.tif.aux.xml"  # XML file path

# Step 1: Buffer the ponds
buffer_ponds(PONDS_GEOJSON, 10, BUFFERED_GEOJSON)

# Step 2: Read the buffered ponds
gdf = gpd.read_file(BUFFERED_GEOJSON)

# **Detect Farm ID Automatically**
farm_id = gdf["farm_id"].iloc[0] if "farm_id" in gdf.columns else "Unknown"

# Step 3: Search for relevant Landsat images
selected_images = search_stac_images(gdf)

# Step 4: Calculate NWI indices and find the first year when NWI ≥ 1
nwi_medians_df, first_nwi_above_1_year_df = process_nwi(selected_images, gdf)

# Ensure first_nwi_above_1_year_df is a DataFrame
if first_nwi_above_1_year_df is None or not isinstance(first_nwi_above_1_year_df, pd.DataFrame):
    first_nwi_above_1_year_df = pd.DataFrame(columns=['pond_id', 'nwi_first_year'])

# Step 5: Parse LULC labels from the XML file
lulc_labels = parse_lulc_labels(LULC_XML_FILE)

# Step 6: Assign previous LULC classes
lulc_df = assign_previous_lulc_class(BUFFERED_GEOJSON, nwi_medians_df, lulc_labels)

# Ensure lulc_df is a DataFrame
if not isinstance(lulc_df, pd.DataFrame):
    lulc_df = pd.DataFrame(columns=['pond_id', 'previous_class'])

# Step 7: Merge data and generate final output
final_output = {
    "farmid": farm_id,
    "noofponds": len(gdf),
    "ponds": []
}

# Convert all data to a single structured JSON format
for _, row in gdf.iterrows():
    pond_id = row["pond_id"]

    # Fetch first NWI year from DataFrame
    first_year_entry = first_nwi_above_1_year_df[first_nwi_above_1_year_df['pond_id'] == pond_id]
    first_year = first_year_entry['nwi_first_year'].values[0] if not first_year_entry.empty else "no data"

    # Fetch LULC class from DataFrame
    lulc_entry = lulc_df[lulc_df['pond_id'] == pond_id]
    previous_class_code = lulc_entry['previous_class'].values[0] if not lulc_entry.empty else None
    previous_class = lulc_labels.get(str(previous_class_code), "Unknown") if previous_class_code else "no data"

    # Append to final output JSON
    final_output["ponds"].append({
        "id": pond_id,
        "Probable Year of Change": first_year,
        "Previous Class": previous_class,
        "Present Class": "Pond"  # Default present class
    })

# Save final output JSON
with open(FINAL_OUTPUT_JSON, "w") as f:
    json.dump(final_output, f, indent=4)

print(f"Final output saved to {FINAL_OUTPUT_JSON}")
