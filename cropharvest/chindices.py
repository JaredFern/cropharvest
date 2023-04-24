from cropharvest.datasets import CropHarvest, CropHarvestLabels
from cropharvest.bands import BANDS

import requests
import tempfile
import argparse
import h5py
import vegind
import numpy as np

# ==================================================================
# Suggestion: Make copy of CropHarvest dataset
#
# This script generates new index data based on Sentinal-2 data and 
# writes back to the original file.
# ==================================================================

DATA_DIR = "cropdata"

NEW_INDICES = ["ExG", "ExR", "SAVI", "GNDVI", "GRVI"]

def main(args):
    DATA_DIR = args.datapath

    # Download datasets if necessary
    evaluation_datasets = CropHarvest.create_benchmark_datasets(DATA_DIR)
    evaluation_datasets

    # Get labels
    labels = CropHarvestLabels(DATA_DIR)
    labels_geojson = labels.as_geojson()

    # Get data for each row 
    num_handled = 0
    expected_data_shape = (12, len(BANDS))
    for i in range(len(labels_geojson)):
        # Load the .h5 file
        to_data = labels._path_from_row(labels_geojson.iloc[i])
        try: data = h5py.File(to_data, "r")
        except: continue

        # Get the data array -> should have data for 
        # each band (B2, B3, etc.) for all 12 months.
        bands_data = data.get("array")[:]
        data.close()
        assert bands_data.shape == expected_data_shape , f'{to_data} has mis-shaped data? {bands_data.shape}'

        # Transpose so the rows are by category
        bands_data_transpose = bands_data.transpose()

        # Calculate new indices
        new_per_index_data = []
        for index in NEW_INDICES:
            indexf = getattr(vegind, index)
            assert indexf
            new_per_index_data.append(indexf(bands_data_transpose))

        # Append and reorganize
        new_data = np.concatenate(new_per_index_data)
        final_data = np.transpose(np.reshape(np.append(bands_data_transpose, new_data), (-1, 12)))

        # Write back
        updated = h5py.File(to_data, 'w')
        updated.create_dataset('array', data=final_data)
        updated.close()
        num_handled += 1
    
    # Debugging
    print("Added", NEW_INDICES, "for", num_handled, "labels!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'datapath',
        type=str,
        help="Path to CropHarvest dataset"
    )
   
    args = parser.parse_args()
    main(args)
