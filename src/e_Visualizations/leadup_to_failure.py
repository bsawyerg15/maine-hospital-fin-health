import plotly.graph_objects as go


def plot_leadup_to_failure(df, title=None, yaxis_title=None, row_label_col=None, mean=None, std=None):
    """
    Plot each row of a dataframe as a time series, where columns represent time points.

    Parameters
    ----------
    df : pd.DataFrame
        Rows are entities (e.g. hospitals), columns are time points.
    title : str, optional
        Chart title.
    yaxis_title : str, optional
        Y-axis label.
    row_label_col : str, optional
        Column to use as the trace name for each row. If None, uses the index.
    mean : float, optional
        Constant mean value to draw as a horizontal reference line.
    std : float, optional
        Constant standard deviation. Shades a band of [mean-std, mean+std] when
        provided alongside mean.

    Returns
    -------
    plotly.graph_objects.Figure
    """
    if row_label_col is not None:
        plot_df = df.drop(columns=[row_label_col])
        labels = df[row_label_col].astype(str)
    else:
        plot_df = df
        labels = df.index.astype(str)

    x = list(plot_df.columns)

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
            name="Mean",
        ))

    for label, (_, row) in zip(labels, plot_df.iterrows()):
        fig.add_trace(go.Scatter(
            x=x,
            y=row.values,
            mode="lines+markers",
            name=str(label),
            line=dict(color='lightgray'),
            marker=dict(color='lightgray')
        ))

    fig.update_layout(
        title=title,
        yaxis_title=yaxis_title,
        xaxis_title=None,
    )

    return fig
