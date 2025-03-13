import json
import os

DATA_DIR = "data"

def combine_json_outputs():
    """Merge the JSON outputs from main_1.py and main_2.py into a single structured response."""
    
    json1_path = os.path.join(DATA_DIR, "output_main_1.json")
    json2_path = os.path.join(DATA_DIR, "output_main_2.json")
    final_output_path = os.path.join(DATA_DIR, "final_output.json")

    # Ensure both files exist before proceeding
    if not os.path.exists(json1_path) or not os.path.exists(json2_path):
        raise FileNotFoundError("One or both JSON output files are missing.")

    # Load the JSON outputs
    with open(json1_path, "r") as f1, open(json2_path, "r") as f2:
        data1 = json.load(f1)
        data2 = json.load(f2)

    # Ensure 'Images' field exists in final output
    final_output = {
        "farmid": data1.get("farmid", "Unknown"),
        "noofponds": data1.get("noofponds", 0),
        "ponds": data1.get("ponds", []),
        "Images": data2.get("Images", [])  # Assuming main_2 produces an 'Images' field
    }

    # Save final merged JSON
    with open(final_output_path, "w") as f:
        json.dump(final_output, f, indent=4)

    print(f"Final JSON output saved to {final_output_path}")
    return final_output

