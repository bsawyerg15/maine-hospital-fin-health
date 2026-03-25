import math
import plotly.graph_objects as go
from a_Config.global_constants import get_measure_tickformat


def plot_hospital_time_series(
    hospital_da,
    pop_mean_da=None,
    pop_std_da=None,
    hospital_name=None,
    measure=None,
    title=None,
    tickformat=None,
):
    """
    Line chart of a single hospital's measure over time, with an optional
    non-failed population mean ± 1 std dev band.

    Parameters
    ----------
    hospital_da : xr.DataArray
        DataArray with dim 'year'. Values for the selected hospital and measure.
    pop_mean_da : xr.DataArray, optional
        Population (non-failed) mean by year. May include a 'Total' entry — filtered internally.
    pop_std_da : xr.DataArray, optional
        Population (non-failed) std dev by year.
    hospital_name : str, optional
    measure : str, optional
        Used for y-axis tick formatting.
    title : str, optional
    """
    hosp_year_set = set(
        y for y in hospital_da.coords['year'].values
        if str(y) != 'Total' and not math.isnan(float(hospital_da.sel(year=y)))
    )

    fig = go.Figure()

    if pop_mean_da is not None and pop_std_da is not None:
        pop_year_set = set(y for y in pop_mean_da.coords['year'].values if str(y) != 'Total')
        hosp_min, hosp_max = min(hosp_year_set), max(hosp_year_set)
        pop_years = sorted(y for y in pop_year_set if hosp_min <= y <= hosp_max)
        px = [str(y) for y in pop_years]
        means = [float(pop_mean_da.sel(year=y)) for y in pop_years]
        stds = [float(pop_std_da.sel(year=y)) for y in pop_years]
        uppers = [m + s for m, s in zip(means, stds)]
        lowers = [m - s for m, s in zip(means, stds)]

        fig.add_trace(go.Scatter(
            x=px, y=uppers,
            mode='lines', line=dict(width=0),
            showlegend=False, hoverinfo='skip',
            connectgaps=True,
        ))
        fig.add_trace(go.Scatter(
            x=px, y=lowers,
            mode='lines', line=dict(width=0),
            fill='tonexty',
            fillcolor='rgba(180, 180, 180, 0.2)',
            showlegend=False, hoverinfo='skip',
            connectgaps=True,
        ))
        fig.add_trace(go.Scatter(
            x=px, y=means,
            mode='lines',
            line=dict(color='gray', dash='dash', width=1.5),
            name='Population Mean +/- 1 Std. Dev.',
            connectgaps=True,
        ))

    years = sorted(hosp_year_set)
    x = [str(y) for y in years]
    hosp_values = [float(hospital_da.sel(year=y)) for y in years]

    fig.add_trace(go.Scatter(
        x=x, y=hosp_values,
        mode='lines+markers',
        name=hospital_name or 'Hospital',
        line=dict(color='steelblue', width=2),
        marker=dict(color='steelblue', size=6),
    ))

    fig.update_layout(
        title=title,
        xaxis_title='Year',
        yaxis=dict(
            title=measure,
            tickformat=tickformat if tickformat is not None else (get_measure_tickformat(measure) if measure else None),
        ),
    )

    return fig
