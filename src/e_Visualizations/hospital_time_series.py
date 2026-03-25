import plotly.graph_objects as go
from a_Config.global_constants import get_measure_tickformat


def plot_hospital_time_series(
    hospital_da,
    pop_mean_da=None,
    pop_std_da=None,
    hospital_name=None,
    measure=None,
    title=None,
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
    years = sorted(y for y in hospital_da.coords['year'].values if str(y) != 'Total')
    x = [str(y) for y in years]
    hosp_values = [float(hospital_da.sel(year=y)) for y in years]

    fig = go.Figure()

    if pop_mean_da is not None and pop_std_da is not None:
        pop_year_set = set(pop_mean_da.coords['year'].values)
        pop_years = [y for y in years if y in pop_year_set]
        px = [str(y) for y in pop_years]
        means = [float(pop_mean_da.sel(year=y)) for y in pop_years]
        stds = [float(pop_std_da.sel(year=y)) for y in pop_years]
        uppers = [m + s for m, s in zip(means, stds)]
        lowers = [m - s for m, s in zip(means, stds)]

        fig.add_trace(go.Scatter(
            x=px, y=uppers,
            mode='lines', line=dict(width=0),
            showlegend=False, hoverinfo='skip',
        ))
        fig.add_trace(go.Scatter(
            x=px, y=lowers,
            mode='lines', line=dict(width=0),
            fill='tonexty',
            fillcolor='rgba(70, 130, 180, 0.2)',
            showlegend=False, hoverinfo='skip',
        ))
        fig.add_trace(go.Scatter(
            x=px, y=means,
            mode='lines',
            line=dict(color='steelblue', dash='dash', width=1.5),
            name='Population Mean +/- 1 Std. Dev.',
        ))

    fig.add_trace(go.Scatter(
        x=x, y=hosp_values,
        mode='lines+markers',
        name=hospital_name or 'Hospital',
        line=dict(color='firebrick', width=2),
        marker=dict(color='firebrick', size=6),
    ))

    fig.update_layout(
        title=title,
        xaxis_title='Year',
        yaxis=dict(
            title=measure,
            tickformat=get_measure_tickformat(measure) if measure else None,
        ),
    )

    return fig
