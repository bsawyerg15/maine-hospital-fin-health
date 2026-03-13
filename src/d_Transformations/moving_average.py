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
