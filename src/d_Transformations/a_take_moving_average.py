import numpy as np
import xarray as xr

from a_Config.enumerations.change_type_enum import ChangeType


def take_moving_average(da: xr.DataArray, num_years: int, changeType: ChangeType = ChangeType.ARITHMETIC) -> xr.DataArray:
    """
    Computes a rolling moving average over the year dimension.

    Requires exactly num_years consecutive non-NaN observations to produce a
    value (no partial windows).

    If changeType is specified as arithmetic, it will take the simple moving average.
    If changeType is geometric, it will take the geometric mean over n periods as:
        exp(mean(ln(1 + r))) - 1

    Args:
        da: DataArray with a 'year' dimension.
        num_years: Window size for the rolling average.

    Returns:
        DataArray of same shape where each year contains the moving average
        ending on that year, or NaN if fewer than num_years observations exist.
    """
    if num_years > da.sizes['year']:
        return xr.full_like(da, fill_value=np.nan)
    
    if changeType == ChangeType.ARITHMETIC:
        return da.rolling(year=num_years, min_periods=num_years).mean()
    else:
        log_da = np.log(1 + da)
        return np.exp(log_da.rolling(year=num_years, min_periods=num_years).mean()) - 1