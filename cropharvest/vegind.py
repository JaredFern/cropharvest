# ========================================
# Calculations for new vegetative indices
# ========================================

from cropharvest.bands import BANDS
import numpy as np
import warnings

def ExG(data: np.ndarray) -> np.ndarray:
    # Excess Green Index: 2g - r - b => 2 * B3 - B4 - B2
    # - https://www.techforwildlife.com/blog/2019/1/22/analysing-drone-and-satellite-imagery-using-vegetation-indices
    #
    # @data -> Full 18 x 12 data, majored by category (e.g. bands)
    # return -> 1 x 12 result of the index calculation

    # Fetch
    B2 = data[BANDS.index("B2")]
    B3 = data[BANDS.index("B3")]
    B4 = data[BANDS.index("B4")]

    # Compute
    ExG_result = (2 * B3) - B4 - B2
    return ExG_result


def ExR(data: np.ndarray) -> np.ndarray:
    # Excess Red Index: (1.4r - g) / (g + r + b) => (1.4 * B4 - B3) / (B3 + B4 + B2)
    # - https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6381699/table/Tab6/
    #
    # @data -> Full 18 x 12 data, majored by category (e.g. bands)
    # return -> 1 x 12 result of the index calculation

    # Fetch
    B2 = data[BANDS.index("B2")]
    B3 = data[BANDS.index("B3")]
    B4 = data[BANDS.index("B4")]

    # Compute
    ExR_result = (1.4 * B4 - B3) / (B3 + B4 + B2)
    return ExR_result


def SAVI(data: np.ndarray) -> np.ndarray:
    # Soil Adjusted Vegetation Index: [(NIR - R) / (NIR + R + L)] * (1 + L) => [(B8 – B4) / (B8 + B4 + L)] * (1 + L)
    # - https://www.techforwildlife.com/blog/2019/1/22/analysing-drone-and-satellite-imagery-using-vegetation-indices
    # - Most formulas online use Red instead of Green wavelengths (like listed in update slides) w/ different arithmetic
    # - L is an adjustment factor (https://en.wikipedia.org/wiki/Soil-adjusted_vegetation_index)
    # - L is chosen manually to 0.4 (based on default settings across Sentinel-2 processing software online)
    #
    # @data -> Full 18 x 12 data, majored by category (e.g. bands)
    # return -> 1 x 12 result of the index calculation

    # Fetch
    L = 0.4
    B4 = data[BANDS.index("B4")]
    B8 = data[BANDS.index("B8")]

    # Compute
    SAVI_result = (B8 - B4) / (B8 + B4 + L) * (1 + L)
    return SAVI_result
    

def GNDVI(data: np.ndarray) -> np.ndarray:
    # Green Normalized Vegetative Index: (NIR - G) / (NIR + G) => B8 - B3
    # - https://custom-scripts.sentinel-hub.com/custom-scripts/sentinel-2/gndvi/
    #
    # @data -> Full 18 x 12 data, majored by category (e.g. bands)
    # return -> 1 x 12 result of the index calculation

    # Fetch
    B3 = data[BANDS.index("B3")]
    B8 = data[BANDS.index("B8")]

    # Compute
    GNDVI_result = (B8 - B3) / (B8 + B3)
    return GNDVI_result


def GRVI(data: np.ndarray) -> np.ndarray:
    # Green Red Vegetative Index: (G - R) / (G + R) => (B3 - B4) / (B3 - B4)
    # - https://www.mdpi.com/2072-4292/2/10/2369
    #
    # @data -> Full 18 x 12 data, majored by category (e.g. bands)
    # return -> 1 x 12 result of the index calculation

    # Fetch
    B3 = data[BANDS.index("B3")]
    B4 = data[BANDS.index("B4")]

    # Compute
    GRVI_result = (B3 - B4) / (B3 + B4)
    return GRVI_result




