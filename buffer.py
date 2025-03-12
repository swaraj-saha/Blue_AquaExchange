import geopandas as gpd
import os
from pyproj import CRS

def buffer_ponds(input_geojson, buffer_distance, output_geojson):
    os.makedirs(os.path.dirname(output_geojson), exist_ok=True)

    # Read input GeoJSON
    gdf = gpd.read_file(input_geojson)
    
    # Ensure CRS is WGS84 before processing
    gdf = gdf.set_crs("EPSG:4326", allow_override=True)

    # Define UTM Zone 44N
    utm_crs = "EPSG:32644"

    # Convert to UTM for accurate buffering
    gdf_utm = gdf.to_crs(utm_crs)
    
    # Debug: Log areas before buffering
    gdf_utm["area_m2"] = gdf_utm.area
    for _, row in gdf_utm.iterrows():
        print(f"Pond {row['pond_id']}: Area {row['area_m2']:.2f} m², Bounds: {row.geometry.bounds}")

    # Apply buffer
    gdf_utm["geometry"] = gdf_utm.geometry.buffer(buffer_distance)
    
    # Convert back to WGS84
    buffered_gdf = gdf_utm.to_crs("EPSG:4326")
    
    # Save to GeoJSON
    buffered_gdf.to_file(output_geojson, driver='GeoJSON')

    print(f"Buffered file saved at: {output_geojson}")

if __name__ == "__main__":
    buffer_ponds("input/ponds.geojson", 10, "output/buffered_ponds.geojson")
