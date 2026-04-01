import xarray as xr
from functools import reduce
from a_Config.global_constants import DERIVE_RATIOS


def derive_ratios(da: xr.DataArray) -> xr.DataArray:
    """
    Computes derived financial ratio measures and returns a DataArray
    containing only the derived ratios.

    NaN propagates naturally through arithmetic: if any component is NaN
    for a given (organization, state, year), the ratio is NaN.

    Args:
        da: DataArray with dims (organization, state, measure, year).

    Returns:
        DataArray with the same dims except the measure dimension contains
        only the derived ratio names.
    """
    available = set(da.coords['measure'].values)
    ratio_slices = []

    for ratio_name, group in DERIVE_RATIOS.groupby('Measure'):
        required = group[~group['Optional?']]['Sub-Measure']
        if not all(m in available for m in required):
            continue

        num_group = group[group['Numerator or Denominator'] == 'Numerator']
        den_group = group[group['Numerator or Denominator'] == 'Denominator']

        def component_sum(sub_group):
            terms = []
            for _, row in sub_group.iterrows():
                if row['Optional?'] and row['Sub-Measure'] not in available:
                    continue
                term = da.sel(measure=row['Sub-Measure']) * row['Multiplier']
                if row['Optional?']:
                    term = term.fillna(0)
                terms.append(term)
            return reduce(lambda a, b: a + b, terms)

        ratio = component_sum(num_group) / component_sum(den_group)
        ratio_slices.append(ratio.expand_dims(measure=[ratio_name]))

    if not ratio_slices:
        return da.isel(measure=[]).rename({'measure': 'measure'})
    return xr.concat(ratio_slices, dim='measure')
