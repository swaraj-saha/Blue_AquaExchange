import json
import os

# Load the JSON file
with open("C:/Users/rivur/Documents/SS_GLX/AquaExchange/pondBoundaries_5.json", "r") as f:
    data = json.load(f)

# Ensure the output directory exists
output_dir = "C:/Users/rivur/Documents/SS_GLX/AquaExchange/Output_geojson_test/5_farms"
os.makedirs(output_dir, exist_ok=True)

# Process each farm
for farm in data:
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
            "properties": {
                "pond_id": pond["id"]
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [coordinates]
            }
        }
        geojson["features"].append(feature)

    # Save to GeoJSON file
    output_path = os.path.join(output_dir, f"{farm_id}.geojson")
    with open(output_path, "w") as f:
        json.dump(geojson, f, indent=4)

    print(f"Saved: {output_path}")
