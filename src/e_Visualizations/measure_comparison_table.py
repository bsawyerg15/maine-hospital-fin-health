import numpy as np
import pandas as pd
import xarray as xr
from matplotlib.colors import LinearSegmentedColormap
from pandas.io.formats.style import Styler

from a_Config.global_constants import get_measure_tickformat

# Soft diverging palette: muted red → white → muted blue
_SOFT_RWB = LinearSegmentedColormap.from_list(
    'soft_rwb', ['#d46a6a', '#ffffff', '#6a9fd4']
)


def calc_measure_comparison_table(
    aggregate_ds: xr.Dataset,
    ma_aggregate_ds: xr.Dataset,
    failed_aggregate_ds: xr.Dataset,
    failed_ma_aggregate_ds: xr.Dataset,
    measures: list[str],
) -> Styler:
    """
    Build a styled nested DataFrame comparing operational vs. failed hospital
    means for every measure, for both Endpoint and MA variants.

    Parameters
    ----------
    aggregate_ds : xr.Dataset
        Output of ``calc_population_aggregates`` on the endpoint variable.
        Dims: (population, measure, year); year coordinate includes 'Total'.
    ma_aggregate_ds : xr.Dataset
        Same as ``aggregate_ds`` but for the moving-average variable.
    failed_aggregate_ds : xr.Dataset
        Output of ``calc_aggregates`` on the failed dataset (endpoint).
        Dims: (measure, relative_year); relative_year includes 'Total'.
    failed_ma_aggregate_ds : xr.Dataset
        Same as ``failed_aggregate_ds`` but for the moving-average variable.
    measures : list[str]
        Measures to include, in display order.

    Returns
    -------
    pandas Styler
        Index: measure names (filtered to *measures*).
        Columns: MultiIndex with outer level ('Endpoint', 'MA') and inner
        level ('Operational Mean', 'Failed Mean', 'Diff').
        Diff = Operational Mean − Failed Mean.
        Each column has a blue-high / white-mid / red-low gradient.
        Values are formatted per measure (% or float).
    """
    available = set(aggregate_ds.coords['measure'].values)
    measures = [m for m in measures if m in available]

    endpoint_op = aggregate_ds['mean'].sel(population='non_failed', measure=measures, year='Total').values
    endpoint_fail = failed_aggregate_ds['mean'].sel(measure=measures, relative_year='Total').values
    ma_op = ma_aggregate_ds['mean'].sel(population='non_failed', measure=measures, year='Total').values
    ma_fail = failed_ma_aggregate_ds['mean'].sel(measure=measures, relative_year='Total').values

    columns = pd.MultiIndex.from_tuples([
        ('Endpoint', 'Operational Mean'),
        ('Endpoint', 'Failed Mean'),
        ('Endpoint', 'Diff'),
        ('MA', 'Operational Mean'),
        ('MA', 'Failed Mean'),
        ('MA', 'Diff'),
    ])

    data = np.column_stack([
        endpoint_op,
        endpoint_fail,
        endpoint_op - endpoint_fail,
        ma_op,
        ma_fail,
        ma_op - ma_fail,
    ])

    df = pd.DataFrame(data, index=measures, columns=columns)

    pct_measures = [m for m in df.index if get_measure_tickformat(m) == '.1%']
    float_measures = [m for m in df.index if get_measure_tickformat(m) != '.1%']

    styler = df.style
    if pct_measures:
        styler = styler.background_gradient(
            cmap=_SOFT_RWB, axis=0, vmin=-0.3, vmax=0.3,
            subset=pd.IndexSlice[pct_measures, :],
        )
    if float_measures:
        styler = styler.background_gradient(
            cmap=_SOFT_RWB, axis=1,
            subset=pd.IndexSlice[float_measures, :],
        )

    for measure in df.index:
        plotly_fmt = get_measure_tickformat(measure)
        fmt = '{:.1%}' if plotly_fmt == '.1%' else '{:.2f}'
        styler = styler.format(fmt, na_rep='—', subset=pd.IndexSlice[measure, :])

    # White background for NaN cells so the gradient doesn't bleed through
    styler = styler.applymap(lambda v: 'background-color: #d3d3d3; color: #888' if pd.isna(v) else '')

    return styler
