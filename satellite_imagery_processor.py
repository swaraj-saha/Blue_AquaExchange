import os
import json
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import box, shape
import geopandas as gpd
import rasterio
from rasterio.mask import mask
import cv2
from pystac_client import Client
import planetary_computer

def process_satellite_imagery(geojson_path, output_dir="output_images", buffer_size=1500, dpi=300):
    """
    Process satellite imagery (Landsat and Sentinel-2) and generate FCC images for specified years.
    
    Args:
        geojson_path (str): Path to the GeoJSON file defining the Area of Interest (AOI).
        output_dir (str): Directory to save the output FCC images.
        buffer_size (int): Buffer size in meters around the AOI for imagery retrieval.
        dpi (int): DPI for saving high-quality images.
    
    Returns:
        dict: JSON-compatible dictionary with dates and image file paths.
    """
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Load and process AOI
    aoi = gpd.read_file(geojson_path).to_crs(epsg=32644)
    geom = aoi.geometry.iloc[0]
    min_x, min_y, max_x, max_y = aoi.total_bounds
    expanded_bbox = box(min_x - buffer_size, min_y - buffer_size, max_x + buffer_size, max_y + buffer_size)
    buffr_aoi_gdf = gpd.GeoDataFrame(geometry=[expanded_bbox], crs=aoi.crs)

    # Helper functions
    def contrast_stretch(band):
        mean_val = np.nanmean(band)
        std_val = np.nanstd(band)
        min_val, max_val = mean_val - (2 * std_val), mean_val + (2 * std_val)
        band = np.clip(band, min_val, max_val)
        return (band - min_val) / (max_val - min_val)

    def bilinear_resample(image, scale=2.0):
        height, width = image.shape[:2]
        new_size = (int(height * scale), int(width * scale))
        return cv2.resize(image, new_size, cv2.INTER_LINEAR)

    def process_band(band):
        return bilinear_resample(contrast_stretch(band), scale=2)

    # Fetch Landsat imagery
    landsat_catalog = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")
    landsat_time_range = "2000-01-01/2016-12-31"
    landsat_search = landsat_catalog.search(
        collections=["landsat-c2-l2"],
        intersects=buffr_aoi_gdf.to_crs("epsg:4326").geometry.iloc[0],
        datetime=landsat_time_range,
        query={"platform": {"neq": "landsat-7"}}
    )
    landsat_items = landsat_search.item_collection()
    fully_covering_landsat = [
        item for item in landsat_items
        if shape(item.geometry).contains(buffr_aoi_gdf.to_crs("epsg:4326").geometry.iloc[0])
    ]

    target_years_landsat = {2001, 2007, 2016}
    items_by_year_landsat = {}
    for item in fully_covering_landsat:
        year = datetime.strptime(item.properties['datetime'], '%Y-%m-%dT%H:%M:%S.%fZ').year
        if year in target_years_landsat:
            items_by_year_landsat.setdefault(year, []).append(item)

    selected_landsat_items = []
    for year in sorted(items_by_year_landsat.keys()):
        images = sorted(items_by_year_landsat[year], key=lambda img: img.properties['eo:cloud_cover'])
        if images:
            selected_landsat_items.append(images[0])

    # Fetch Sentinel-2 imagery
    sentinel_catalog = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")
    sentinel_time_range = "2018-01-01/2024-12-31"
    sentinel_search = sentinel_catalog.search(
        collections=["sentinel-2-l2a"],
        intersects=buffr_aoi_gdf.to_crs("epsg:4326").geometry.iloc[0],
        datetime=sentinel_time_range
    )
    sentinel_items = sentinel_search.item_collection()
    fully_covering_sentinel = [
        item for item in sentinel_items
        if shape(item.geometry).contains(buffr_aoi_gdf.to_crs("epsg:4326").geometry.iloc[0])
    ]

    target_years_sentinel = {2020, 2024}
    items_by_year_sentinel = {}
    for item in fully_covering_sentinel:
        year = datetime.strptime(item.properties['datetime'], '%Y-%m-%dT%H:%M:%S.%fZ').year
        if year in target_years_sentinel:
            items_by_year_sentinel.setdefault(year, []).append(item)

    selected_sentinel_items = []
    for year in sorted(items_by_year_sentinel.keys()):
        images = sorted(items_by_year_sentinel[year], key=lambda img: img.properties['eo:cloud_cover'])
        if images:
            selected_sentinel_items.append(images[0])

    # Process and save images
    output_data = {"images": []}

    def process_and_save_image(item, bands_dict, title_prefix, output_dir, aoi):
        date = item.properties['datetime'][:10]
        masked_bands = {}
        for key, band_url in bands_dict.items():
            with rasterio.open(band_url) as src:
                aoi_rep = buffr_aoi_gdf.to_crs(src.crs)
                band, _ = mask(src, aoi_rep.geometry, crop=True)
                masked_bands[key] = band.squeeze()

        processed_bands = {key: process_band(band) for key, band in masked_bands.items()}
        false_color = np.dstack([processed_bands["nir"], processed_bands["red"], processed_bands["green"]])
        minx, miny, maxx, maxy = aoi_rep.total_bounds

        fig, ax = plt.subplots(figsize=(8, 8))
        ax.imshow(false_color, extent=[minx, maxx, miny, maxy])
        aoi.boundary.plot(ax=ax, edgecolor="yellow", linewidth=2)
        ax.set_xticks([]), ax.set_yticks([])
        ax.set_xticklabels([]), ax.set_yticklabels([])
        plt.title(f"{title_prefix} - {date}")

        img_path = os.path.join(output_dir, f"{date}.png")
        fig.savefig(img_path, dpi=dpi, bbox_inches='tight')
        plt.close(fig)

        return {"date": date, "image_path": img_path}

    # Process Landsat images
    for item in selected_landsat_items:
        bands = {
            "nir": planetary_computer.sign(item.assets['nir08'].href),
            "red": planetary_computer.sign(item.assets['red'].href),
            "green": planetary_computer.sign(item.assets['green'].href),
        }
        result = process_and_save_image(item, bands, "FCC Image Landsat", output_dir, aoi)
        output_data["images"].append(result)

    # Process Sentinel-2 images
    for item in selected_sentinel_items:
        bands = {
            "nir": planetary_computer.sign(item.assets['B08'].href),
            "red": planetary_computer.sign(item.assets['B04'].href),
            "green": planetary_computer.sign(item.assets['B03'].href),
        }
        result = process_and_save_image(item, bands, "FCC Image Sentinel-2", output_dir, aoi)
        output_data["images"].append(result)

    # Sort images by date
    output_data["images"] = sorted(output_data["images"], key=lambda x: x["date"])
    
    return output_data

