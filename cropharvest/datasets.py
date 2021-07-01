from pathlib import Path
import geopandas
import numpy as np
import h5py

from cropharvest.countries import BBox
from cropharvest.utils import download_from_url, filter_geojson, deterministic_shuffle, read_labels
from cropharvest.config import LABELS_FILENAME, DEFAULT_SEED, TEST_REGIONS, TEST_DATASETS
from cropharvest.columns import NullableColumns, RequiredColumns
from cropharvest.engineer import TestInstance
from cropharvest import countries

from typing import Dict, List, Optional, Tuple, Generator


class BaseDataset:
    def __init__(self, root, download: bool, download_url: str, filename: str):
        self.root = Path(root)
        if not self.root.is_dir():
            raise NotADirectoryError(f"{root} should be a directory.")

        path_to_data = self.root / filename

        if download:
            if path_to_data.exists():
                print("Files already downloaded.")
            else:
                download_from_url(download_url, str(path_to_data))

        if not path_to_data.exists():
            raise FileNotFoundError(
                f"{path_to_data} does not exist, it can be downloaded by setting download=True"
            )

    def __getitem__(self, index: int):
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError


class CropHarvestLabels(BaseDataset):
    url = "https://zenodo.org/record/5021762/files/labels.geojson?download=1"

    def __init__(self, root, download=False):
        super().__init__(root, download, download_url=self.url, filename=LABELS_FILENAME)
        self._labels = read_labels(self.root)

    def as_geojson(self) -> geopandas.GeoDataFrame:
        return self._labels

    def __getitem__(self, index: int):
        return self._labels.iloc[index]

    def __len__(self) -> int:
        return len(self._labels)

    def _path_from_row(self, row: geopandas.GeoSeries) -> Path:
        return (
            self.root
            / f"features/arrays/{row[RequiredColumns.INDEX]}_{row[RequiredColumns.DATASET]}.h5"
        )

    def _dataframe_to_paths(self, df: geopandas.GeoDataFrame) -> List[Path]:
        return [self._path_from_row(row) for _, row in df.iterrows()]

    def construct_positive_and_negative_paths(
        self,
        bounding_box: Optional[BBox],
        target_label: Optional[str],
        filter_test: bool,
        balance_negative_crops: bool,
    ) -> Tuple[List[Path], List[Path]]:
        gpdf = self.as_geojson()
        if filter_test:
            gpdf = gpdf[gpdf[RequiredColumns.IS_TEST] == False]
        if bounding_box is not None:
            gpdf = filter_geojson(gpdf, bounding_box)

        is_null = gpdf[NullableColumns.LABEL].isnull()
        is_crop = gpdf[RequiredColumns.IS_CROP] == True

        if target_label is not None:
            positive_labels = gpdf[gpdf[NullableColumns.LABEL] == target_label]
            target_label_is_crop = positive_labels.iloc[0][RequiredColumns.IS_CROP]

            is_target = gpdf[NullableColumns.LABEL] == target_label

            if not target_label_is_crop:
                # if the target label is a non crop class (e.g. pasture),
                # then we can just collect all classes which either
                # 1) are crop, or 2) are a different non crop class (e.g. forest)
                negative_labels = gpdf[((is_null & is_crop) | (~is_null & ~is_target))]
                negative_paths = self._dataframe_to_paths(negative_labels)
            else:
                # otherwise, the target label is a crop. If balance_negative_crops is
                # true, then we want an equal number of (other) crops and non crops in
                # the negative labels
                negative_non_crop_labels = gpdf[~is_crop]
                negative_other_crop_labels = gpdf[(is_crop & ~is_null & ~is_target)]
                negative_non_crop_paths = self._dataframe_to_paths(negative_non_crop_labels)
                negative_paths = self._dataframe_to_paths(negative_other_crop_labels)

                if balance_negative_crops:
                    negative_paths.extend(
                        deterministic_shuffle(negative_non_crop_paths, DEFAULT_SEED)[
                            : len(negative_paths)
                        ]
                    )
                else:
                    negative_paths.extend(negative_non_crop_paths)
        else:
            # otherwise, we will just filter by crop and non crop
            positive_labels = gpdf[is_crop]
            negative_labels = gpdf[~is_crop]
            negative_paths = self._dataframe_to_paths(negative_labels)

        positive_paths = self._dataframe_to_paths(positive_labels)

        return [x for x in positive_paths if x.exists()], [x for x in negative_paths if x.exists()]


class CropHarvestTifs(BaseDataset):
    def __init__(self, root, download=False):
        super().__init__(root, download, download_url="", filename="")

    @classmethod
    def from_labels(cls):
        pass


class CropHarvest(BaseDataset):
    "Dataset consisting of satellite data and associated labels"

    def __init__(
        self,
        root,
        bbox: BBox,
        target_label: Optional[str] = None,
        balance_negative_crops: bool = True,
        test_identifier: Optional[str] = None,
        download=False,
    ):
        super().__init__(root, download, download_url="", filename="")

        self.labels = CropHarvestLabels(root)
        self.bbox = bbox
        self.target_label = target_label if target_label is not None else "crop"

        positive_paths, negative_paths = self.labels.construct_positive_and_negative_paths(
            bbox, target_label, filter_test=True, balance_negative_crops=balance_negative_crops
        )

        self.filepaths: List[Path] = positive_paths + negative_paths
        self.positive_indices: List[int] = list(range(len(positive_paths)))
        self.negative_indices: List[int] = list(
            range(len(positive_paths), len(positive_paths) + len(negative_paths))
        )
        self.y_vals: List[int] = [1] * len(positive_paths) + [0] * len(negative_paths)

        self.test_identifier: Optional[str] = test_identifier

    def __len__(self) -> int:
        return len(self.filepaths)

    def __getitem__(self, index: int) -> Tuple[np.ndarray, int]:
        hf = h5py.File(self.filepaths[index], "r")
        return hf.get("array")[:], self.y_vals[index]

    def test_data(self) -> Generator[Tuple[str, TestInstance], None, None]:
        all_relevant_files = list(
            (self.root / "test_features").glob(f"{self.test_identifier}*.h5")
        )
        if len(all_relevant_files) == 0:
            raise RuntimeError(f"Missing test data {self.test_identifier}*.h5")
        for filepath in all_relevant_files:
            hf = h5py.File(filepath, "r")
            test_array = TestInstance.load_from_h5(hf)
            yield filepath.stem, test_array

    @classmethod
    def create_benchmark_datasets(cls, root, balance_negative_crops: bool = True) -> List:

        output_datasets: List = []

        for identifier, bbox in TEST_REGIONS.items():
            country, crop, _, _ = identifier.split("_")

            if f"{country}_{crop}" not in [x.id for x in output_datasets]:
                country_bboxes = countries.get_country_bbox(country)
                for country_bbox in country_bboxes:
                    if country_bbox.contains_bbox(bbox):
                        output_datasets.append(
                            cls(
                                root,
                                country_bbox,
                                crop,
                                balance_negative_crops,
                                f"{country}_{crop}",
                            )
                        )

        for country, test_dataset in TEST_DATASETS.items():
            # TODO; for now, the only country here is Togo, which
            # only has one bounding box. In the future, it might
            # be nice to confirm its the right index (maybe by checking against
            # some points in the test h5py file?)
            country_bbox = countries.get_country_bbox(country)[0]
            output_datasets.append(
                cls(root, country_bbox, None, balance_negative_crops, test_dataset)
            )
        return output_datasets

    @classmethod
    def from_labels_and_tifs(cls, labels: CropHarvestLabels, tifs: CropHarvestTifs):
        "Creates CropHarvest dataset from CropHarvestLabels and CropHarvestTifs"
        pass

    def __repr__(self) -> str:
        class_name = f"CropHarvest{'Eval' if self.test_identifier is not None else ''}"
        return f"{class_name}({self.bbox.name}, {self.target_label}, {self.test_identifier})"

    @property
    def id(self) -> str:
        return f"{self.bbox.name}_{self.target_label}"
