import xarray as xr
from d_Transformations.calc_changes import calc_period_over_period_change
from d_Transformations.moving_average import take_geometric_moving_average


def run_change_pipeline(ds: xr.Dataset, ma_years: int) -> xr.Dataset:
    """
    Computes period-over-period percent changes and their geometric moving average.

    Pipeline order:
    1. Compute percent change and log change for each base measure.
    2. Compute geometric moving average of the percent changes.
       Geometric MA is used (not arithmetic) because percent changes compound
       multiplicatively: geometric_ma = exp(mean(ln(1 + pct_change))) - 1.

    Args:
        ds: Dataset from to_dataset(), with a 'value' variable of shape
            (organization, state, measure, year) and a 'year_failed'
            coordinate of shape (organization, state).
        ma_years: Rolling window size for the geometric moving average.

    Returns:
        Dataset with 'endpoint' (raw pct_change_value) and 'ma' (geometric MA)
        variables, both with shape (organization, state, measure, year), plus
        the 'year_failed' coordinate carried over from the input.
    """
    change_ds = calc_period_over_period_change(ds)
    pct_da = change_ds['pct_change_value']
    ma_da = take_geometric_moving_average(pct_da, ma_years)

    return xr.Dataset(
        {'endpoint': pct_da, 'ma': ma_da},
        coords={'year_failed': ds['year_failed']},
    )
