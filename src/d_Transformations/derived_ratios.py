import xarray as xr
from functools import reduce
from a_Config.global_constants import DERIVE_RATIOS


def derive_ratios(da: xr.DataArray) -> xr.DataArray:
    """
    Computes derived financial ratio measures and returns a new DataArray
    with the measure dimension extended to include them.

    NaN propagates naturally through arithmetic: if any component is NaN
    for a given (organization, state, year), the ratio is NaN.

    Args:
        da: DataArray with dims (organization, state, measure, year).

    Returns:
        DataArray with the same dims, measure dimension extended to include
        all computable derived ratio names appended at the end.
    """
    available = set(da.coords['measure'].values)
    result = da.copy()
    new_slices = []

    for ratio_name, group in DERIVE_RATIOS.groupby('Measure'):
        if not all(m in available for m in group['Sub-Measure']):
            continue

        num_group = group[group['Numerator or Denominator'] == 'Numerator']
        den_group = group[group['Numerator or Denominator'] == 'Denominator']

        def component_sum(sub_group):
            terms = [
                da.sel(measure=row['Sub-Measure']) * row['Multiplier']
                for _, row in sub_group.iterrows()
            ]
            # Standard addition propagates NaN: if any term is NaN the
            # result is NaN, matching the min_count behaviour from pandas.
            return reduce(lambda a, b: a + b, terms)

        ratio = component_sum(num_group) / component_sum(den_group)

        if ratio_name in available:
            result.loc[dict(measure=ratio_name)] = ratio.values
        else:
            new_slices.append(ratio.expand_dims(measure=[ratio_name]))

    if new_slices:
        result = xr.concat([result] + new_slices, dim='measure')

    return result
