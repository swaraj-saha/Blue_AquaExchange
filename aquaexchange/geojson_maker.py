import json
import os

def create_geojson(farm_data, output_folder):
    """
    Converts farm JSON data into GeoJSON format and saves it.

    Parameters:
    - farm_data (list): JSON data containing farms and ponds.
    - output_folder (str): Path to save the generated GeoJSON files.

    Returns:
    - list: Paths of the saved GeoJSON files.
    """
    os.makedirs(output_folder, exist_ok=True)
    saved_files = []

    # Process each farm
    for farm in farm_data:
        farm_id = farm["farmid"]
        geojson = {
            "type": "FeatureCollection",
            "features": []
        }

        for pond in farm["ponds"]:
            coordinates = [
                [float(point["lng"]), float(point["lat"])] for point in pond["boundaries"].values()
            ]
            # Close the polygon by repeating the first point at the end
            coordinates.append(coordinates[0])

            feature = {
                "type": "Feature",
                "properties": {"pond_id": pond["id"]},
                "geometry": {"type": "Polygon", "coordinates": [coordinates]},
            }
            geojson["features"].append(feature)

        # Save to GeoJSON file
        output_path = os.path.join(output_folder, f"{farm_id}.geojson")
        with open(output_path, "w") as f:
            json.dump(geojson, f, indent=4)
        
        saved_files.append(output_path)

    return saved_files
