import numpy as np
import pandas as pd
import rasterio
from rasterio.mask import mask
import planetary_computer
import geopandas as gpd

def calculate_nwi(blue, nir, swir16, swir22):
    """
    Calculate Normalized Water Index (NWI).
    
    Formula: (Blue - (NIR + SWIR1 + SWIR2)) / (Blue + (NIR + SWIR1 + SWIR2))
    
    Args:
        blue (numpy array): Blue band.
        nir (numpy array): Near-Infrared band.
        swir16 (numpy array): Shortwave Infrared (1.6µm) band.
        swir22 (numpy array): Shortwave Infrared (2.2µm) band.

    Returns:
        numpy array: Computed NWI values.
    """
    denominator = blue + (nir + swir16 + swir22)
    with np.errstate(divide='ignore', invalid='ignore'):
        nwi = np.where(denominator != 0, (blue - (nir + swir16 + swir22)) / denominator, np.nan)
    return nwi

def process_nwi(selected_items_by_year, aoi_gdf):
    """
    Process NWI for selected images and determine the first year when NWI >= 1 for each pond.
    
    Args:
        selected_items_by_year (dict): Dictionary with years as keys and image metadata as values.
        aoi_gdf (GeoDataFrame): GeoDataFrame containing pond polygons with 'pond_id'.

    Returns:
        DataFrame: Contains 'pond_id', 'nwi_first_year', 'median_nwi'.
    """
    nwi_results = []

    for _, pond in aoi_gdf.iterrows():
        pond_id = pond["pond_id"]
        pond_geom = pond["geometry"]

        first_nwi_above_1_year = None
        yearly_nwi_medians = {}

        for year, images in selected_items_by_year.items():
            yearly_nwi = []

            for item in images:
                try:
                    # Get signed asset URLs
                    blue_band = planetary_computer.sign(item.assets['blue'].href)
                    nir_band = planetary_computer.sign(item.assets['nir08'].href)
                    swir16_band = planetary_computer.sign(item.assets['swir16'].href)
                    swir22_band = planetary_computer.sign(item.assets['swir22'].href)
                except KeyError:
                    continue  # Skip if any required band is missing

                # Read raster data
                with rasterio.open(blue_band) as blue_src, \
                     rasterio.open(nir_band) as nir_src, \
                     rasterio.open(swir16_band) as swir16_src, \
                     rasterio.open(swir22_band) as swir22_src:

                    pond_geom_rep = gpd.GeoSeries([pond_geom], crs=aoi_gdf.crs).to_crs(blue_src.crs)

                    blue, _ = mask(blue_src, pond_geom_rep.geometry, crop=True)
                    nir, _ = mask(nir_src, pond_geom_rep.geometry, crop=True)
                    swir16, _ = mask(swir16_src, pond_geom_rep.geometry, crop=True)
                    swir22, _ = mask(swir22_src, pond_geom_rep.geometry, crop=True)

                    # Compute NWI
                    nwi = calculate_nwi(blue, nir, swir16, swir22)

                    # Flatten and filter valid values
                    valid_nwi = nwi.flatten()
                    valid_nwi = valid_nwi[~np.isnan(valid_nwi)]
                    yearly_nwi.extend(valid_nwi)

            if yearly_nwi:
                nwi_median = np.nanmedian(yearly_nwi)
                yearly_nwi_medians[year] = nwi_median

                if first_nwi_above_1_year is None and nwi_median >= 1:
                    first_nwi_above_1_year = year

        # Store results for this pond
        nwi_results.append({
            "pond_id": pond_id,
            "nwi_first_year": first_nwi_above_1_year if first_nwi_above_1_year is not None else np.nan,
            "median_nwi": yearly_nwi_medians if yearly_nwi_medians else None
        })

    return pd.DataFrame(nwi_results)
