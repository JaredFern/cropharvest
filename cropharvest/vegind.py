# ========================================
# Calculations for new vegetative indices
#
# Much of the calculations are based on: 
# - https://www.techforwildlife.com/blog/2019/1/22/analysing-drone-and-satellite-imagery-using-vegetation-indices
# ========================================

from cropharvest.bands import BANDS
import numpy as np

def ExG(data: np.ndarray) -> np.ndarray:
    # Excess Green Index: 2g - r - b => (2 * B3) - (B4 + B2)
    #
    # @data -> Full 18 x 12 data, majored by category (e.g. bands)
    # return -> 1 x 12 result of the index calculation

    # Fetch
    B2 = data[BANDS.index("B2")]
    B3 = data[BANDS.index("B3")]
    B4 = data[BANDS.index("B4")]

    # Compute
    ExG_result = (2 * B3) - (B4 + B2)
    return ExG_result



def ExR(data: np.ndarray) -> np.ndarray:
    # Excess Red Index: 1.4r - g => 1.4 * B4 - B3 ... extrapolating based on ExG
    #
    # @data -> Full 18 x 12 data, majored by category (e.g. bands)
    # return -> 1 x 12 result of the index calculation

    # Fetch
    B3 = data[BANDS.index("B3")]
    B4 = data[BANDS.index("B4")]

    # Compute
    ExR_result = 1.4 * B4 - B3
    return ExR_result


def SAVI(data: np.ndarray) -> np.ndarray:
    # Soil Adjusted Vegetation Index: [(NIR - R) / (NIR + R + L)] * (1 + L) => [(B8 – B4) / (B8 + B4 + L)] * (1 + L)
    # - Most formulas online use Red instead of Green wavelengths (like listed in update slides) w/ different arithmetic
    # - L is an adjustment factor (https://en.wikipedia.org/wiki/Soil-adjusted_vegetation_index)
    # - As a rule-of-thumb, L is often set statically to 0.5
    #
    # @data -> Full 18 x 12 data, majored by category (e.g. bands)
    # return -> 1 x 12 result of the index calculation

    # Fetch
    L = 0.5
    B4 = data[BANDS.index("B4")]
    B8 = data[BANDS.index("B8")]

    # Compute
    SAVI_result = ((B8 - B4) / (B8 + B4 + L)) * (1 + L)
    return SAVI_result
    

def GNDVI(data: np.ndarray) -> np.ndarray:
    # Green Normalized Vegetative Index: NIR - G => B8 - B3 ... extrapolating from SAVI
    #
    # @data -> Full 18 x 12 data, majored by category (e.g. bands)
    # return -> 1 x 12 result of the index calculation

    # Fetch
    B3 = data[BANDS.index("B3")]
    B8 = data[BANDS.index("B8")]

    # Compute
    GNDVI_result = B8 - B3
    return GNDVI_result






