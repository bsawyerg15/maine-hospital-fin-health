import plotly.graph_objects as go


def plot_leadup_to_failure(da, mean, std, title=None, yaxis_title=None):
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
        yaxis_title=yaxis_title,
        xaxis_title=None,
    )

    return fig
