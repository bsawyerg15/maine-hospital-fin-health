import numpy as np
import xarray as xr


def calc_period_over_period_change(ds: xr.Dataset, var: str, ma_years: int) -> xr.Dataset:
    """
    Computes period-over-period changes for a single variable.

    Returns a Dataset with:
        value        = raw values of var
        ln_measure     = log(value)
        ln_pct_change  = diff of ln_value (ln(t) - ln(t-1))
        pct_change     = exp(ln_pct_change)
        ma_pct_change  = exp(rolling mean of ln_pct_change over ma_years)
        cum_pct_change = exp(cumulative sum of ln_pct_change)

    Args:
        ds:       Dataset with a 'year' dimension containing var.
        var:      Name of the data variable to process.
        ma_years: Window size for the moving average of ln_pct_change.

    Returns:
        Dataset with the six variables above.
    """
    da = ds[var]
    ln_value = np.log(da)
    ln_pct_change = ln_value - ln_value.shift(year=1)

    ma_ln = ln_pct_change.rolling(year=ma_years, min_periods=1).mean()

    cum_ln = ln_pct_change.cumsum(dim='year', skipna=True)

    return xr.Dataset(
        {
            'value': da,
            'ln_value': ln_value,
            'ln_pct_change': ln_pct_change,
            'pct_change': np.exp(ln_pct_change) - 1,
            'ma_pct_change': np.exp(ma_ln) - 1,
            'cum_pct_change': np.exp(cum_ln) - 1,
        },
        coords=ds.coords,
    )
