import numpy as np
import xarray as xr


def calc_arith_changes(ds: xr.Dataset, var: str, ma_years: int) -> xr.Dataset:
    """
    Computes period-over-period arithmetic changes for a single variable.

    Returns a Dataset with:
        value            = raw values of var
        arith_change     = value(t) - value(t-1)
        ma_arith_change  = rolling mean of arith_change over ma_years
        cum_arith_change = cumulative sum of arith_change

    Args:
        ds:       Dataset with a 'year' dimension containing var.
        var:      Name of the data variable to process.
        ma_years: Window size for the moving average of arith_change.

    Returns:
        Dataset with the four variables above.
    """
    da = ds[var]
    arith_change = da - da.shift(year=1)

    if ma_years > arith_change.sizes['year']:
        ma_arith = xr.full_like(arith_change, fill_value=np.nan)
    else:
        ma_arith = arith_change.rolling(year=ma_years, min_periods=ma_years).mean()

    cum_arith = arith_change.cumsum(dim='year', skipna=True)

    return xr.Dataset(
        {
            'value': da,
            'arith_change': arith_change,
            'ma_arith_change': ma_arith,
            'cum_arith_change': cum_arith,
        },
        coords=ds.coords,
    )
