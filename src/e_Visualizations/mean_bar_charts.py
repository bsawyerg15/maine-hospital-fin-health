import numpy as np
import plotly.graph_objects as go


def plot_mean_bar_chart(series_list, labels=None, title=None, yaxis_title=None):
    """
    Plot a bar chart of means with standard deviation error bars.

    Parameters
    ----------
    series_list : list of pd.Series or array-like
        Each element is a series of values. Mean and std are computed per element.
    labels : list of str, optional
        Bar labels. Defaults to "Series 0", "Series 1", etc.
    title : str, optional
        Chart title.
    yaxis_title : str, optional
        Y-axis label.

    Returns
    -------
    plotly.graph_objects.Figure
    """
    if labels is None:
        labels = [f"Series {i}" for i in range(len(series_list))]

    means = []
    stds = []
    for s in series_list:
        if isinstance(s, tuple):
            means.append(s[0])
            stds.append(s[1])
        else:
            values = np.asarray(s, dtype=float)
            values = values[~np.isnan(values)]
            means.append(np.mean(values))
            stds.append(np.std(values, ddof=1) if len(values) > 1 else 0.0)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=labels,
        y=means,
        mode="markers",
        error_y=dict(type="data", array=stds, visible=True),
        marker=dict(color="steelblue", size=10),
    ))

    fig.update_layout(
        title=title,
        yaxis_title=yaxis_title,
        xaxis_title=None,
    )

    return fig
