import numpy as np
import pandas as pd
import plotly.graph_objects as go
import xarray as xr
from a_Config.global_constants import get_measure_tickformat, ALL_RATIOS


def plot_measure_scatter(x_da: xr.DataArray, y_da: xr.DataArray, year_failed: xr.DataArray, y_lag: int = 0) -> go.Figure:
    """
    Scatter plot of x_da vs y_da, one point per (hospital, year).

    Failed hospitals are shown in red; operational hospitals in blue. Hover
    displays the hospital name, state, and year.

    Parameters
    ----------
    x_da : xr.DataArray
        DataArray with dims (organization, state, year). The 'measure' scalar
        coordinate is used as the x-axis label.
    y_da : xr.DataArray
        DataArray with dims (organization, state, year). The 'measure' scalar
        coordinate is used as the y-axis label.
    year_failed : xr.DataArray
        DataArray with dims (organization, state). Non-null values indicate
        failed hospitals.
    """
    measure_x = x_da.coords['measure'].item() if 'measure' in x_da.coords else (x_da.name or 'X')
    measure_y = y_da.coords['measure'].item() if 'measure' in y_da.coords else (y_da.name or 'Y')
    if y_lag != 0:
        lag_sign = '+' if y_lag > 0 else ''
        measure_y = f'{measure_y} (lag {lag_sign}{y_lag}y)'

    x_series = x_da.to_series().rename('x')
    y_series = y_da.to_series().rename('y')

    df = x_series.to_frame().join(y_series, how='inner').dropna().reset_index()

    yf_df = year_failed.to_series().rename('year_failed').reset_index()
    df = df.merge(yf_df, on=['organization', 'state'], how='left')
    df['failed'] = df['year_failed'].notna()

    hover = (
        '<b>%{customdata[0]}</b><br>'
        'State: %{customdata[1]}<br>'
        'Year: %{customdata[2]}'
        '<extra></extra>'
    )

    non_failed = df[~df['failed']]
    failed = df[df['failed']]

    def _fit(subset):
        coeffs = np.polyfit(subset['x'], subset['y'], 1)
        x_range = np.linspace(subset['x'].min(), subset['x'].max(), 200)
        y_fit = np.polyval(coeffs, x_range)
        ss_res = np.sum((subset['y'] - np.polyval(coeffs, subset['x'])) ** 2)
        ss_tot = np.sum((subset['y'] - subset['y'].mean()) ** 2)
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float('nan')
        return x_range, y_fit, r2

    x_range, y_fit, r2 = _fit(df)
    x_range_failed, y_fit_failed, r2_failed = _fit(failed)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=non_failed['x'],
        y=non_failed['y'],
        mode='markers',
        name='Operational',
        marker=dict(color='steelblue', size=6, opacity=0.55),
        customdata=non_failed[['organization', 'state', 'year']].values,
        hovertemplate=hover,
    ))

    fig.add_trace(go.Scatter(
        x=failed['x'],
        y=failed['y'],
        mode='markers',
        name='Failed',
        marker=dict(color='firebrick', size=7, opacity=0.8),
        customdata=failed[['organization', 'state', 'year']].values,
        hovertemplate=hover,
    ))

    fig.add_trace(go.Scatter(
        x=x_range,
        y=y_fit,
        mode='lines',
        name=f'Best Fit — All (R²={r2:.3f})',
        line=dict(color='gray', dash='dash', width=1.5),
        hoverinfo='skip',
    ))

    fig.add_trace(go.Scatter(
        x=x_range_failed,
        y=y_fit_failed,
        mode='lines',
        name=f'Best Fit — Failed (R²={r2_failed:.3f})',
        line=dict(color='firebrick', dash='dash', width=1.5),
        hoverinfo='skip',
    ))

    fig.update_layout(
        title=f'{measure_x} vs {measure_y}',
        xaxis=dict(title=measure_x, tickformat=get_measure_tickformat(measure_x, measure_x not in ALL_RATIOS)),
        yaxis=dict(title=measure_y, tickformat=get_measure_tickformat(measure_y, measure_y not in ALL_RATIOS)),
        width=600,
        height=600,
        legend=dict(x=0.01, y=0.99),
    )

    return fig
