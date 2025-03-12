import geopandas as gpd
import pandas as pd
import rasterio
import xml.etree.ElementTree as ET
import numpy as np

# Mapping LULC years to corresponding raster files
LULC_FILES = {
    1999: "C:/Users/rivur/Documents/SS_GLX/AquaExchange/LULC_AP/drive-download-20250312T040019Z-001/lulc_with_labels_1999.tif"  # Ensure this is correctly set
}

def parse_lulc_labels(xml_file):
    """Parse the LULC XML metadata file and return a dictionary mapping raster values to class names."""
    tree = ET.parse(xml_file)
    root = tree.getroot()

    class_mapping = {}
    for class_item in root.findall(".//Class"):  # Adjust based on XML structure
        class_value = int(class_item.find("Value").text)
        class_name = class_item.find("Name").text
        class_mapping[str(class_value)] = class_name  # Store keys as strings

    return class_mapping

def get_previous_lulc_year(nwi_first_year):
    """Determine the most recent LULC year before the first NWI observation."""
    years = sorted(LULC_FILES.keys(), reverse=True)
    for year in years:
        if nwi_first_year and year < nwi_first_year:
            return year
    return None  # No previous LULC year available

def get_lulc_class(geom, lulc_year, xml_file):
    """Get LULC class for a pond using the LULC raster and return human-readable class names."""
    lulc_file = LULC_FILES.get(lulc_year)
    if not lulc_file:
        return "no data"

    class_mapping = parse_lulc_labels(xml_file)  # Read XML for class labels

    with rasterio.open(lulc_file) as src:
        lon, lat = geom.centroid.x, geom.centroid.y
        raster_value = next(src.sample([(lon, lat)]))[0]  # Extract the first value

        if raster_value is not None and not np.isnan(raster_value):
            return class_mapping.get(str(int(raster_value)), "Unknown Class")  # Convert to int & use as str key

    return "no data"

def assign_previous_lulc_class(ponds_geojson, nwi_df, xml_file):
    """Assign previous LULC class based on NWI year and return a DataFrame."""
    gdf = gpd.read_file(ponds_geojson).to_crs("EPSG:4326")

    results = []
    for _, row in gdf.iterrows():
        pond_id = row["pond_id"]
        first_year_entry = nwi_df.loc[nwi_df["pond_id"] == pond_id, "nwi_first_year"]

        first_year = int(first_year_entry.values[0]) if not first_year_entry.empty else None

        if first_year is None:
            lulc_class = "no data"
        else:
            prev_lulc_year = get_previous_lulc_year(first_year)
            lulc_class = get_lulc_class(row["geometry"], prev_lulc_year, xml_file) if prev_lulc_year else "no data"

        results.append({"pond_id": pond_id, "previous_class": lulc_class})

    return pd.DataFrame(results)
