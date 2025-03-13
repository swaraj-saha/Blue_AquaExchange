import geopandas as gpd
import pandas as pd
import rasterio
import xml.etree.ElementTree as ET
import numpy as np

LULC_FILES = {1999: "data/lulc_with_labels_1999.tif"}

def parse_lulc_labels(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    return {row[0].text.strip(): row[1].text.strip() for row in root.findall(".//GDALRasterAttributeTable/Row")}

def get_previous_lulc_year(nwi_first_year):
    return next((y for y in sorted(LULC_FILES.keys(), reverse=True) if y < nwi_first_year), None) if nwi_first_year else None

def get_lulc_class(geom, lulc_year, class_mapping):
    if lulc_year not in LULC_FILES:
        return None, None
    with rasterio.open(LULC_FILES[lulc_year]) as src:
        raster_value = next(src.sample([(geom.centroid.x, geom.centroid.y)]))[0]
        return (int(raster_value), class_mapping.get(str(int(raster_value)), "Unknown Class")) if raster_value else (None, None)

def assign_previous_lulc_class(ponds_geojson, nwi_df, xml_file):
    gdf = gpd.read_file(ponds_geojson).to_crs("EPSG:4326")
    class_mapping = parse_lulc_labels(xml_file)

    results = [{"pond_id": row["pond_id"], "lulc_value": *get_lulc_class(row["geometry"], get_previous_lulc_year(int(nwi_df.loc[nwi_df["pond_id"] == row["pond_id"], "nwi_first_year"].values[0])) if not nwi_df.empty else None, class_mapping)} for _, row in gdf.iterrows()]
    
    return pd.DataFrame(results)
