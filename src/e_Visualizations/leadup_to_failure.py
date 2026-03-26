import numpy as np
import plotly.graph_objects as go
from a_Config.global_constants import get_measure_tickformat


def plot_leadup_to_failure(da, mean, std, title=None, yaxis_title=None, measure=None):
    """
    Plot each failed hospital as a time series of Value vs Relative Year.

    Parameters
    ----------
    da : xr.DataArray
        DataArray with dims (organization, relative_year). Typically
        failed_ds['endpoint'].sel(measure=selected_measure).
    mean : float
        Constant mean of the operational population, drawn as a reference line.
    std : float
        Standard deviation of the operational population, shaded as a band.
    title : str, optional
        Chart title.
    yaxis_title : str, optional
        Y-axis label.
    """
    def rel_year_label(n):
        return 'T' if n == 0 else f'T - {abs(n)}'

    rel_years = sorted(int(y) for y in da.coords['relative_year'].values)
    x = [rel_year_label(n) for n in rel_years]

    fig = go.Figure()

    if mean is not None and std is not None:
        upper = [mean + std] * len(x)
        lower = [mean - std] * len(x)
        fig.add_trace(go.Scatter(
            x=x, y=upper,
            mode="lines", line=dict(width=0),
            showlegend=False, hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=x, y=lower,
            mode="lines", line=dict(width=0),
            fill="tonexty",
            fillcolor="rgba(70, 130, 180, 0.2)",
            showlegend=False, hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=x, y=[mean] * len(x),
            mode="lines",
            line=dict(color="steelblue", dash="dash", width=1.5),
            name="Operational Mean",
        ))

    for org in da.coords['organization'].values:
        org_da = da.sel(organization=org)
        values = [org_da.sel(relative_year=y).item() for y in rel_years]
        fig.add_trace(go.Scatter(
            x=x,
            y=values,
            mode="lines+markers",
            name=str(org),
            line=dict(color='lightgray'),
            marker=dict(color='lightgray'),
        ))

    fig.update_layout(
        title=title,
        yaxis=dict(title=yaxis_title, tickformat=get_measure_tickformat(measure) if measure else None),
        xaxis_title=None,
    )

    return fig


def plot_cum_leadup_to_failure(da, mean, std, title=None, yaxis_title=None, measure=None):
    """
    Plot each failed hospital's cumulative percent change, re-indexed to 0 at
    the first relative year, with a geometric-mean reference line and a
    log-normal cone for the operational population.

    Parameters
    ----------
    da : xr.DataArray
        DataArray with dims (organization, relative_year) containing cumulative
        percent changes (e.g. 0.10 = 10%).
    mean : float
        Per-period mean percent change of the operational population.
    std : float
        Per-period std dev of percent changes of the operational population.
    title : str, optional
    yaxis_title : str, optional
    """
    def rel_year_label(n):
        return 'T' if n == 0 else f'T - {abs(n)}'

    rel_years = sorted(int(y) for y in da.coords['relative_year'].values)
    x = [rel_year_label(n) for n in rel_years]
    ns = list(range(len(rel_years)))  # 0, 1, 2, … steps from first relative year
                                      # n=0 at earliest relative year → all series start at 0

    fig = go.Figure()

    if mean is not None and std is not None:
        ln_mean = np.log1p(mean)
        ln_std = np.log1p(std)

        mean_line = [(1 + mean) ** n - 1 for n in ns]
        upper = [np.exp(n * ln_mean + np.sqrt(n) * ln_std) - 1 for n in ns]
        lower = [np.exp(n * ln_mean - np.sqrt(n) * ln_std) - 1 for n in ns]

        fig.add_trace(go.Scatter(
            x=x, y=upper,
            mode="lines", line=dict(width=0),
            showlegend=False, hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=x, y=lower,
            mode="lines", line=dict(width=0),
            fill="tonexty",
            fillcolor="rgba(70, 130, 180, 0.2)",
            showlegend=False, hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=x, y=mean_line,
            mode="lines",
            line=dict(color="steelblue", dash="dash", width=1.5),
            name="Operational Mean",
        ))

    for org in da.coords['organization'].values:
        org_da = da.sel(organization=org)
        values_plus_one = [1 + org_da.sel(relative_year=y).item() for y in rel_years]
        baseline = values_plus_one[0]
        reindexed = [-1 + v / baseline for v in values_plus_one]
        fig.add_trace(go.Scatter(
            x=x,
            y=reindexed,
            mode="lines+markers",
            name=str(org),
            line=dict(color='lightgray'),
            marker=dict(color='lightgray'),
        ))

    fig.update_layout(
        title=title,
        yaxis=dict(title=yaxis_title, tickformat=get_measure_tickformat(measure, is_pct=True) if measure else None),
        xaxis_title=None,
    )

    return fig
