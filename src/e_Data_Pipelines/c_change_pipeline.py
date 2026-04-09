import xarray as xr
from a_Config.enumerations.interface_fields_enum import InterfaceFields
from a_Config.fin_statement_model_utils import ALL_RATIOS, LINE_ITEMS
from d_Transformations.d_calc_pct_changes import calc_pct_changes
from d_Transformations.e_calc_arith_changes import calc_arith_changes

_PCT_DROP = {'value', 'ln_value', 'ln_pct_change'}
_ARITH_DROP = {'value'}


def run_change_pipeline(ds: xr.Dataset, ma_years: int) -> xr.Dataset:
    """
    Compute period-over-period changes for all measures, routing each to the
    appropriate method based on measure type:
      - Line items  → geometric (% change via log-differencing)
      - Ratios      → arithmetic (absolute difference)

    Returns a Dataset with dimensions (organization, state, measure, year) and
    data variables mapped to InterfaceFields: CHANGE, MA_OF_CHANGE, CUM_CHANGE.
    Measures not in ALL_RATIOS or LINE_ITEMS are silently excluded.

    Args:
        ds:       Dataset with a 'value' data variable and a 'measure' dimension.
        ma_years: Rolling window size for the moving average of changes.
    """
    measures = ds.coords['measure'].values.tolist()
    ratio_measures = [m for m in measures if m in ALL_RATIOS]
    line_item_measures = [m for m in measures if m in LINE_ITEMS]

    parts = []

    if line_item_measures:
        pct_ds = calc_pct_changes(ds.sel(measure=line_item_measures), InterfaceFields.ENDPOINT, ma_years)
        pct_ds = pct_ds.drop_vars(_PCT_DROP & set(pct_ds.data_vars))
        parts.append(pct_ds.rename({
            'pct_change': InterfaceFields.CHANGE,
            'ma_pct_change': InterfaceFields.MA_OF_CHANGE,
            'cum_pct_change': InterfaceFields.CUM_CHANGE,
        }))

    if ratio_measures:
        arith_ds = calc_arith_changes(ds.sel(measure=ratio_measures), InterfaceFields.ENDPOINT, ma_years)
        arith_ds = arith_ds.drop_vars(_ARITH_DROP & set(arith_ds.data_vars))
        parts.append(arith_ds.rename({
            'arith_change': InterfaceFields.CHANGE,
            'ma_arith_change': InterfaceFields.MA_OF_CHANGE,
            'cum_arith_change': InterfaceFields.CUM_CHANGE,
        }))

    return xr.concat(parts, dim='measure')
