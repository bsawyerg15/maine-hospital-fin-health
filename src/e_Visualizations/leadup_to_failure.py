import plotly.graph_objects as go


def plot_leadup_to_failure(df, mean, std, title=None, yaxis_title=None):
    """
    Plot each hospital as a time series of Value vs Relative Year.

    Parameters
    ----------
    df : pd.DataFrame
        Tall DataFrame with (Organization, State, Year) MultiIndex and
        'Value' and 'Relative Year' columns. One row per (hospital, year).
    mean : float, optional
        Constant mean value to draw as a horizontal reference line.
    std : float, optional
        Constant standard deviation. Shades a band of [mean-std, mean+std] when
        provided alongside mean.
    title : str, optional
        Chart title.
    yaxis_title : str, optional
        Y-axis label.

    Returns
    -------
    plotly.graph_objects.Figure
    """
    def rel_year_label(n):
        return 'T' if n == 0 else f'T - {abs(n)}'

    x = [rel_year_label(n) for n in sorted(df['Relative Year'].unique())]

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

    for org in df.index.get_level_values('Organization').unique():
        org_data = df.xs(org, level='Organization').sort_values('Relative Year')
        fig.add_trace(go.Scatter(
            x=org_data['Relative Year'].map(rel_year_label),
            y=org_data['Value'],
            mode="lines+markers",
            name=str(org),
            line=dict(color='lightgray'),
            marker=dict(color='lightgray')
        ))

    fig.update_layout(
        title=title,
        yaxis_title=yaxis_title,
        xaxis_title=None,
    )

    return fig
