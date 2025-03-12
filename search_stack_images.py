from pystac_client import Client
from shapely.geometry import shape
from datetime import datetime

def search_stac_images(aoi, cloud_cover_threshold=20):
    catalog = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")

    # Define the time range and cloud cover filter
    time_range = "1999-05-01/2024-12-31"

    # Perform the search
    search = catalog.search(
        collections=["landsat-c2-l2"],
        intersects=aoi.geometry.iloc[0],
        datetime=time_range,
        # query={"eo:cloud_cover": {"lt": cloud_cover}}
    )

    # Fetch all items
    items = search.item_collection()

    # Filter items to ensure full AOI coverage
    fully_covering_items = []
    for item in items:
        item_geom = shape(item.geometry)  # Convert STAC geometry to Shapely
        if item_geom.contains(aoi.geometry.iloc[0]):  # Ensure image fully covers AOI
            fully_covering_items.append(item)

    # Organize items by year (selecting multiple acquisitions per year)
    items_by_year = {}
    for item in fully_covering_items:
        year = datetime.strptime(item.properties['datetime'], '%Y-%m-%dT%H:%M:%S.%fZ').year
        if year not in items_by_year:
            items_by_year[year] = []  # Store multiple images per year
        items_by_year[year].append(item)

    selected_items_by_year = {}

    for year, images in items_by_year.items():
        selected_items = [img for img in images if img.properties['eo:cloud_cover'] <= cloud_cover_threshold]

        if selected_items:
            # Sort by cloud cover (ascending) to prefer images with lower cloud cover
            selected_items.sort(key=lambda img: img.properties['eo:cloud_cover'])

            # Keep only the first 5 images if more than 5 are available
            selected_items_by_year[year] = selected_items[:5]

    # Print selected images per year
    for year, images in selected_items_by_year.items():
        print(f"\nYear: {year} (Selected {len(images)} images with ≤ {cloud_cover_threshold}% cloud cover)")
        for img in images:
            print(f"  - Date: {img.properties['datetime']} | Cloud Cover: {img.properties['eo:cloud_cover']:.2f}")

    return selected_items_by_year
