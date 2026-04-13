import numpy as np
import plotly.graph_objects as go
from a_Config.global_constants import get_measure_tickformat


def plot_failed_histogram(ds, failed_ds, measure_name, var, ma_years=None, bins=20, title=None,
                          subtitle=None, clip_lower=None, clip_upper=None):
    """
    Plot a dual-axis histogram comparing a population to failed hospitals.

    Parameters
    ----------
    ds : xr.Dataset
        Full financials Dataset with 'endpoint', 'ma', and 'year_failed'.
    failed_ds : xr.Dataset
        Output of create_failed_dataset — indexed by relative_year.
    measure_name : str
        Measure to plot.
    ma_years : int or None
        If set, uses the 'ma' variable; otherwise uses 'endpoint'.
    bins : int
        Number of histogram bins.
    title : str, optional
        Chart title.
    subtitle : str, optional
        Chart subtitle displayed below the title.
    """
    non_failed_values = (
        ds[var].sel(measure=measure_name)
        .where(ds['year_failed'].isnull())
        .values.flatten()
    )
    non_failed_values = non_failed_values[~np.isnan(non_failed_values)]

    if failed_ds and failed_ds.dims:
        failed_values = (
            failed_ds[var].sel(measure=measure_name, relative_year=-1)
            .values.flatten()
        )
        failed_values = failed_values[~np.isnan(failed_values)]
    else:
        failed_values = np.array([])

    if clip_lower is not None or clip_upper is not None:
        lo = clip_lower if clip_lower is not None else -np.inf
        hi = clip_upper if clip_upper is not None else np.inf
        non_failed_values = np.clip(non_failed_values, lo, hi)
        failed_values = np.clip(failed_values, lo, hi)

    all_values = np.concatenate([non_failed_values, failed_values])
    bin_edges = np.histogram_bin_edges(all_values, bins=bins)
    bin_size = bin_edges[1] - bin_edges[0]

    fig = go.Figure()

    fig.add_trace(go.Histogram(
        x=non_failed_values,
        xbins=dict(start=bin_edges[0], end=bin_edges[-1], size=bin_size),
        name="Operational Hospitals" if not ma_years else f"Operational Hospitals ({ma_years}yma)",
        marker_color="steelblue",
        opacity=0.6,
        yaxis="y1",
    ))

    fig.add_trace(go.Histogram(
        x=failed_values,
        xbins=dict(start=bin_edges[0], end=bin_edges[-1], size=bin_size),
        name="Year Failed" if not ma_years else f'{ma_years}yma Prior to Failure',
        marker_color="firebrick",
        opacity=0.7,
        yaxis="y2",
    ))

    is_pct = 'pct' in var
    pct_text = ' (% Chg)' if is_pct else ''
    xaxis_title = f'{measure_name}{pct_text}' if is_pct else measure_name

    fig.update_layout(
        title=dict(text=title or f'Distribution of {measure_name}{pct_text}', subtitle=dict(text=subtitle)),
        xaxis=dict(title=xaxis_title, tickformat=get_measure_tickformat(measure_name, is_pct)),
        yaxis=dict(title="Operational count", title_font=dict(color="steelblue")),
        yaxis2=dict(
            title="Failed count",
            title_font=dict(color="firebrick"),
            overlaying="y",
            side="right",
        ),
        barmode="overlay",
        legend=dict(x=0.8, y=0.95),
    )

    return fig
