import geopandas as gpd
import os

def merge_geojson(input_geojson, output_folder):
    """
    Merge all pond boundaries for a single farm into a single GeoJSON file.

    Args:
        input_geojson (str): Path to the input farm-level GeoJSON file.
        output_folder (str): Path to save the merged GeoJSON.

    Returns:
        str: Path to the merged GeoJSON file.
    """
    os.makedirs(output_folder, exist_ok=True)

    # Load the input GeoJSON file
    gdf = gpd.read_file(input_geojson)

    # Merge all pond boundaries into a single polygon
    merged_boundary = gdf.dissolve().unary_union
    merged_gdf = gpd.GeoDataFrame(geometry=[merged_boundary], crs=gdf.crs)

    # Generate the output file path
    farm_id = os.path.splitext(os.path.basename(input_geojson))[0]
    output_filename = os.path.join(output_folder, f"{farm_id}_merged.geojson")

    # Save the merged GeoJSON
    merged_gdf.to_file(output_filename, driver="GeoJSON")

    print(f"Merged GeoJSON saved: {output_filename}")
    return output_filename
