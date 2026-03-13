import numpy as np
import xarray as xr


def calc_period_over_period_change(ds: xr.Dataset) -> xr.Dataset:
    """
    Computes period-over-period percent change and log change for every
    variable in the Dataset along the 'year' dimension.

    For each variable v:
        pct_change_<v>  = (v - v.shift(year=1)) / v.shift(year=1)
        ln_change_<v>   = ln(v / v.shift(year=1))

    The first year will be NaN for both (no prior period).

    Args:
        ds: Dataset with a 'year' dimension.

    Returns:
        Dataset containing pct_change_* and ln_change_* variables.
    """
    result = {}
    for var in ds.data_vars:
        da = ds[var]
        prior = da.shift(year=1)
        result[f'pct_change_{var}'] = (da - prior) / prior
        result[f'ln_change_{var}'] = np.log(da / prior)
    return xr.Dataset(result, coords=ds.coords)
