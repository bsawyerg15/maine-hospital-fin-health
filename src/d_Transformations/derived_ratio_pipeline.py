import xarray as xr
from d_Transformations.derived_ratios import derive_ratios
from d_Transformations.moving_average import take_moving_average


def run_derived_ratio_pipeline(ds: xr.Dataset, ma_years: int) -> xr.Dataset:
    """
    Computes derived ratio measures from a raw financials Dataset.

    Pipeline order:
    1. Compute moving average of raw base measures.
    2. Derive endpoint ratios from raw measures (numerator / denominator).
    3. Derive MA ratios from MA of raw measures (MA(num) / MA(denom)).

    Step 3 ensures MA ratios are MA(numerator) / MA(denominator),
    not MA(ratio) — these are not equivalent.

    Args:
        ds: Dataset from to_dataset(), with a 'value' variable of shape
            (organization, state, measure, year) and a 'year_failed'
            coordinate of shape (organization, state).
        ma_years: Rolling window size for moving averages.

    Returns:
        Dataset with 'endpoint' and 'ma' variables, both with shape
        (organization, state, measure, year) where measure contains only
        the derived ratio names, plus the 'year_failed' coordinate carried
        over from the input.
    """
    raw_da = ds['value']

    # Step 1: MA of raw base measures
    ma_raw_da = take_moving_average(raw_da, ma_years)

    # Step 2: Derived ratios from raw endpoints
    endpoint_da = derive_ratios(raw_da)

    # Step 3: Derived ratios from MA of raw — MA(num) / MA(denom)
    ma_da = derive_ratios(ma_raw_da)

    return xr.Dataset(
        {'endpoint': endpoint_da, 'ma': ma_da},
        coords={'year_failed': ds['year_failed']},
    )
