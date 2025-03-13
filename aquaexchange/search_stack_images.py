from pystac_client import Client
from shapely.geometry import shape
from datetime import datetime

def search_stac_images(aoi, cloud_cover_threshold=20, collections=None):
    """
    Searches for Landsat and Sentinel-2 images using the STAC API.

    Args:
        aoi (GeoDataFrame): Area of Interest as a GeoDataFrame.
        cloud_cover_threshold (int): Maximum allowable cloud cover percentage.
        collections (list, optional): List of STAC collections to search. Defaults to Landsat and Sentinel.

    Returns:
        dict: Dictionary of images grouped by year.
    """
    catalog = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")

    # Define the time range for image search
    time_range = "1999-05-01/2024-12-31"

    # Default collections if none are provided
    if collections is None:
        collections = ["landsat-c2-l2", "sentinel-2-l2a"]

    # Perform the search
    search = catalog.search(
        collections=collections,
        intersects=aoi.geometry.iloc[0],
        datetime=time_range,
    )

    # Fetch all items
    items = search.item_collection()

    # Filter items that fully cover the AOI
    fully_covering_items = [
        item for item in items if shape(item.geometry).contains(aoi.geometry.iloc[0])
    ]

    # Organize items by year
    items_by_year = {}
    for item in fully_covering_items:
        year = datetime.strptime(item.properties["datetime"], "%Y-%m-%dT%H:%M:%S.%fZ").year
        if year not in items_by_year:
            items_by_year[year] = []
        items_by_year[year].append(item)

    # Select images with the lowest cloud cover (max 5 per year)
    selected_items_by_year = {}
    for year, images in items_by_year.items():
        selected_images = [img for img in images if img.properties["eo:cloud_cover"] <= cloud_cover_threshold]
        
        if selected_images:
            selected_images.sort(key=lambda img: img.properties["eo:cloud_cover"])
            selected_items_by_year[year] = selected_images[:5]  # Keep max 5 per year

    return selected_items_by_year
