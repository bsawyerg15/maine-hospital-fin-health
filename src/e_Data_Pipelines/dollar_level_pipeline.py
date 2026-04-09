import xarray as xr
from a_Config.global_constants import ALL_RATIOS
from d_Transformations.a_take_moving_average import take_moving_average


def run_dollar_level_pipeline(underived_ds: xr.Dataset, ma_years: int) -> xr.Dataset:
    """
    Builds a dollar-level dataset from raw underived financials.

    Pipeline:
    1. Filter to non-ratio measures.
    2. Compute a moving average of the 'value' variable.

    Args:
        underived_ds: Dataset from to_dataset(), with dims (organization, state, measure, year).
        ma_years: Rolling window size for the moving average.

    Returns:
        Dataset with 'value' and 'ma' variables over only the non-ratio measures.
    """
    dollar_measures = [m for m in underived_ds.coords['measure'].values if m not in ALL_RATIOS]
    ds = underived_ds.sel(measure=dollar_measures)
    return ds.assign(ma=take_moving_average(ds['value'], ma_years))
