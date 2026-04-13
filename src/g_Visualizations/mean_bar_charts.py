import plotly.graph_objects as go
from a_Config.global_constants import get_measure_tickformat, ALL_RATIOS


def plot_mean_bar_chart(series_list, labels=None, title=None, subtitle=None, yaxis_title=None, measure=None):
    """
    Plot a bar chart of means with standard deviation error bars.

    Parameters
    ----------
    series_list : list of (mean, std) tuples
        Pre-computed mean and standard deviation for each bar.
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

    means = [s[0] for s in series_list]
    stds = [s[1] for s in series_list]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=labels,
        y=means,
        mode="markers",
        error_y=dict(type="data", array=stds, visible=True),
        marker=dict(color="steelblue", size=10),
    ))

    is_pct = measure not in ALL_RATIOS
    if yaxis_title is None and measure:
        yaxis_title = f'{measure} (% Chg)' if is_pct else measure

    fig.update_layout(
        title=dict(text=title, subtitle=dict(text=subtitle)),
        yaxis=dict(title=yaxis_title, tickformat=get_measure_tickformat(measure, is_pct) if measure else None),
        xaxis_title=None,
    )

    return fig
