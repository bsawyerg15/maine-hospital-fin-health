import numpy as np
import xarray as xr


def take_moving_average(da: xr.DataArray, num_years: int) -> xr.DataArray:
    """
    Computes a rolling moving average over the year dimension.

    Requires exactly num_years consecutive non-NaN observations to produce a
    value (no partial windows).

    Args:
        da: DataArray with a 'year' dimension.
        num_years: Window size for the rolling average.

    Returns:
        DataArray of same shape where each year contains the moving average
        ending on that year, or NaN if fewer than num_years observations exist.
    """
    return da.rolling(year=num_years, min_periods=num_years).mean()


def take_geometric_moving_average(da: xr.DataArray, num_years: int) -> xr.DataArray:
    """
    Computes a rolling geometric moving average of percent-change data.

    For percent changes r, the geometric mean over n periods is:
        exp(mean(ln(1 + r))) - 1

    Requires exactly num_years consecutive non-NaN observations.

    Args:
        da: DataArray of percent changes (e.g. 0.05 = 5%) with a 'year' dimension.
        num_years: Window size for the rolling average.

    Returns:
        DataArray of same shape containing the geometric moving average.
    """
    log_da = np.log(1 + da)
    return np.exp(log_da.rolling(year=num_years, min_periods=num_years).mean()) - 1
