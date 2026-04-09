import xarray as xr
from a_Config.enumerations.interface_fields_enum import InterfaceFields
from d_Transformations.b_derived_ratios import derive_ratios
from e_Data_Pipelines.a_dollar_level_pipeline import run_dollar_level_pipeline


def run_level_pipeline(ds: xr.Dataset, ma_years: int) -> xr.Dataset:
    """
    Produce a unified levels dataset with endpoint and ma fields for all
    measures (dollar line items + derived ratios).

    Pipeline:
    1. Run dollar_level_pipeline to get endpoint and ma for all line items.
    2. Derive endpoint ratios from line-item endpoints (raw values).
    3. Derive MA ratios from line-item MAs — MA(num)/MA(denom), not MA(ratio).
    4. Concatenate dollar and ratio Datasets along the measure dimension.

    Args:
        ds:       Dataset with a 'value' variable and dims
                  (organization, state, measure, year).
        ma_years: Rolling window size for the moving average.

    Returns:
        Dataset with InterfaceFields.ENDPOINT and InterfaceFields.MA variables
        over all measures (line items + derived ratios), plus the year_failed
        coordinate carried from the input.
    """
    # Step 1: dollar levels → endpoint + ma
    dollar_ds = run_dollar_level_pipeline(ds, ma_years)
    dollar_out = xr.Dataset(
        {
            InterfaceFields.ENDPOINT: dollar_ds['value'],
            InterfaceFields.MA: dollar_ds['ma'],
        },
        coords={'year_failed': ds['year_failed']},
    )

    # Steps 2-3: derived ratios pulling from dollar_out so only line-item
    # measures are passed (no pre-existing ratio measures in the input).
    endpoint_ratios = derive_ratios(dollar_out[InterfaceFields.ENDPOINT])
    ma_ratios = derive_ratios(dollar_out[InterfaceFields.MA])
    ratio_out = xr.Dataset(
        {
            InterfaceFields.ENDPOINT: endpoint_ratios,
            InterfaceFields.MA: ma_ratios,
        },
        coords={'year_failed': ds['year_failed']},
    )

    # Step 4: combine
    return xr.concat([dollar_out, ratio_out], dim='measure')
