"""
AquaExchange Package
====================
This package processes farm pond data, buffers ponds, retrieves satellite images, 
calculates NWI indices, assigns LULC classes, and produces structured JSON outputs.
"""

# Import key modules for easier access
from .buffer import buffer_ponds
from .calculate_indices import process_nwi
from .find_previous_lulc import assign_previous_lulc_class
from .geojson_maker import create_geojson
from .merge_geojson import merge_geojson
from .search_stack_images import search_stac_images
from .satellite_imagery_processor import process_satellite_imagery
from .combine_outputs import merge_final_outputs
from .utils import *

# Define package version
__version__ = "1.0.0"
