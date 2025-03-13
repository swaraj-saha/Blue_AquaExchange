import os
import json
import logging
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

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class SatelliteImageryProcessor:
    """
    A class to fetch and process satellite imagery (Landsat & Sentinel-2) for FCC visualization.
    """

    def __init__(self, buffer_size=1500, dpi=300):
        self.buffer_size = buffer_size
        self.dpi = dpi

    def _contrast_stretch(self, band):
        """Apply contrast stretching to enhance image visibility."""
        mean_val = np.nanmean(band)
        std_val = np.nanstd(band)
        min_val, max_val = mean_val - (2 * std_val), mean_val + (2 * std_val)
        band = np.clip(band, min_val, max_val)
        return (band - min_val) / (max_val - min_val)

    def _bilinear_resample(self, image, scale=2.0):
        """Rescale image using bilinear interpolation."""
        height, width = image.shape[:2]
        new_size = (int(height * scale), int(width * scale))
        return cv2.resize(image, new_size, cv2.INTER_LINEAR)

    def _process_band(self, band):
        """Apply contrast stretching and resampling to a band."""
        return self._bilinear_resample(self._contrast_stretch(band), scale=2)

    def _get_aoi(self, geojson_path):
        """Load and buffer the AOI from a GeoJSON file."""
        aoi = gpd.read_file(geojson_path).to_crs(epsg=32644)
        min_x, min_y, max_x, max_y = aoi.total_bounds
        expanded_bbox = box(min_x - self.buffer_size, min_y - self.buffer_size,
                            max_x + self.buffer_size, max_y + self.buffer_size)
        return aoi, gpd.GeoDataFrame(geometry=[expanded_bbox], crs=aoi.crs)

    def _fetch_imagery(self, collection, time_range, target_years, buffer_gdf):
        """Fetch imagery from Microsoft Planetary Computer."""
        catalog = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")
        search = catalog.search(
            collections=[collection],
            intersects=buffer_gdf.to_crs("epsg:4326").geometry.iloc[0],
            datetime=time_range
        )
        items = search.item_collection()
        fully_covering = [
            item for item in items
            if shape(item.geometry).contains(buffer_gdf.to_crs("epsg:4326").geometry.iloc[0])
        ]

        images_by_year = {}
        for item in fully_covering:
            year = datetime.strptime(item.properties['datetime'], '%Y-%m-%dT%H:%M:%S.%fZ').year
            if year in target_years:
                images_by_year.setdefault(year, []).append(item)

        selected_items = []
        for year in sorted(images_by_year.keys()):
            images = sorted(images_by_year[year], key=lambda img: img.properties['eo:cloud_cover'])
            if images:
                selected_items.append(images[0])

        return selected_items

    def _process_and_save_image(self, item, bands_dict, title_prefix, output_dir, buffer_gdf, aoi):
        """Process and save FCC image."""
        date = item.properties['datetime'][:10]
        masked_bands = {}

        for key, band_url in bands_dict.items():
            with rasterio.open(band_url) as src:
                aoi_rep = buffer_gdf.to_crs(src.crs)
                band, _ = mask(src, aoi_rep.geometry, crop=True)
                masked_bands[key] = band.squeeze()

        processed_bands = {key: self._process_band(band) for key, band in masked_bands.items()}
        false_color = np.dstack([processed_bands["nir"], processed_bands["red"], processed_bands["green"]])
        minx, miny, maxx, maxy = aoi_rep.total_bounds

        fig, ax = plt.subplots(figsize=(8, 8))
        ax.imshow(false_color, extent=[minx, maxx, miny, maxy])
        aoi.boundary.plot(ax=ax, edgecolor="yellow", linewidth=2)
        ax.set_xticks([]), ax.set_yticks([])
        plt.title(f"{title_prefix} - {date}")

        img_path = os.path.join(output_dir, f"{date}.png")
        fig.savefig(img_path, dpi=self.dpi, bbox_inches='tight')
        plt.close(fig)

        return {"date": date, "image_path": img_path}

    def process_satellite_imagery(self, geojson_path, output_dir="output_images"):
        """
        Process satellite imagery and generate FCC images for specified years.
        
        Args:
            geojson_path (str): Path to the GeoJSON file defining the AOI.
            output_dir (str): Directory to save the output FCC images.
        
        Returns:
            dict: JSON-compatible dictionary with dates and image file paths.
        """
        os.makedirs(output_dir, exist_ok=True)
        aoi, buffer_gdf = self._get_aoi(geojson_path)

        # Fetch imagery
        logging.info("Fetching Landsat imagery...")
        landsat_items = self._fetch_imagery(
            collection="landsat-c2-l2",
            time_range="2000-01-01/2016-12-31",
            target_years={2001, 2007, 2016},
            buffer_gdf=buffer_gdf
        )

        logging.info("Fetching Sentinel-2 imagery...")
        sentinel_items = self._fetch_imagery(
            collection="sentinel-2-l2a",
            time_range="2018-01-01/2024-12-31",
            target_years={2020, 2024},
            buffer_gdf=buffer_gdf
        )

        output_data = {"images": []}

        # Process Landsat images
        for item in landsat_items:
            bands = {
                "nir": planetary_computer.sign(item.assets['nir08'].href),
                "red": planetary_computer.sign(item.assets['red'].href),
                "green": planetary_computer.sign(item.assets['green'].href),
            }
            result = self._process_and_save_image(item, bands, "FCC Image Landsat", output_dir, buffer_gdf, aoi)
            output_data["images"].append(result)

        # Process Sentinel-2 images
        for item in sentinel_items:
            bands = {
                "nir": planetary_computer.sign(item.assets['B08'].href),
                "red": planetary_computer.sign(item.assets['B04'].href),
                "green": planetary_computer.sign(item.assets['B03'].href),
            }
            result = self._process_and_save_image(item, bands, "FCC Image Sentinel-2", output_dir, buffer_gdf, aoi)
            output_data["images"].append(result)

        output_data["images"] = sorted(output_data["images"], key=lambda x: x["date"])
        return output_data
