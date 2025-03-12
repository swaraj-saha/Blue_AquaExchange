import numpy as np
import pandas as pd
import rasterio
from rasterio.mask import mask
import planetary_computer
import geopandas as gpd

def calculate_nwi(blue, nir, swir16, swir22):
    """
    Calculate Normalized Water Index (NWI).
    """
    denominator = blue + (nir + swir16 + swir22)
    with np.errstate(divide='ignore', invalid='ignore'):
        nwi = np.where(denominator != 0,
                       (blue - (nir + swir16 + swir22)) / denominator,
                       np.nan)
    return nwi

def process_nwi(selected_items_by_year, aoi_gdf):
    """
    Process NWI for selected images and determine the first year when NWI >= 1 for each pond.
    
    Args:
        selected_items_by_year (dict): Dictionary with years as keys and image metadata as values.
        aoi_gdf (GeoDataFrame): GeoDataFrame containing pond polygons with 'pond_id'.

    Returns:
        DataFrame: Contains 'pond_id', 'year', 'nwi_median'.
        DataFrame: Contains 'pond_id' and the first year when NWI >= 1.
    """
    nwi_medians = []
    first_nwi_years = {}

    for _, pond in aoi_gdf.iterrows():  # Process each pond separately
        pond_id = pond["pond_id"]
        pond_geom = pond["geometry"]

        first_nwi_above_1_year = None  # Track the first year when NWI >= 1 for this pond

        for year, images in selected_items_by_year.items():
            yearly_nwi = []

            for item in images:
                # Access asset URLs
                blue_band = planetary_computer.sign(item.assets['blue'].href)
                nir_band = planetary_computer.sign(item.assets['nir08'].href)
                swir16_band = planetary_computer.sign(item.assets['swir16'].href)
                swir22_band = planetary_computer.sign(item.assets['swir22'].href)

                # Open the bands
                with rasterio.open(blue_band) as blue_src, \
                     rasterio.open(nir_band) as nir_src, \
                     rasterio.open(swir16_band) as swir16_src, \
                     rasterio.open(swir22_band) as swir22_src:

                    pond_geom_rep = gpd.GeoSeries([pond_geom], crs=aoi_gdf.crs).to_crs(blue_src.crs)

                    blue, _ = mask(blue_src, pond_geom_rep.geometry, crop=True)
                    nir, _ = mask(nir_src, pond_geom_rep.geometry, crop=True)
                    swir16, _ = mask(swir16_src, pond_geom_rep.geometry, crop=True)
                    swir22, _ = mask(swir22_src, pond_geom_rep.geometry, crop=True)

                    # Calculate NWI
                    nwi = calculate_nwi(blue, nir, swir16, swir22)

                    # Flatten and remove NaNs
                    valid_nwi = nwi.flatten()
                    valid_nwi = valid_nwi[~np.isnan(valid_nwi)]
                    yearly_nwi.extend(valid_nwi)

            if yearly_nwi:
                nwi_median = np.nanmedian(yearly_nwi)
                nwi_medians.append({'pond_id': pond_id, 'year': year, 'nwi_median': nwi_median})

                # Check if this is the first year where NWI >= 1
                if first_nwi_above_1_year is None and nwi_median >= 1:
                    first_nwi_above_1_year = year

        # Store first NWI ≥ 1 year for this pond
        first_nwi_years[pond_id] = first_nwi_above_1_year

    return pd.DataFrame(nwi_medians), pd.DataFrame(list(first_nwi_years.items()), columns=['pond_id', 'nwi_first_year'])
