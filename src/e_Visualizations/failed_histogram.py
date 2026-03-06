import numpy as np
import plotly.graph_objects as go


def plot_failed_histogram(population_df, failed_df, pop_column, failed_column, bins=20, title=None):
    """
    Plot a dual-axis histogram comparing a population to failed hospitals.

    Parameters
    ----------
    population_df : pd.DataFrame
        Full population of hospitals.
    failed_df : pd.DataFrame
        Subset of failed hospitals.
    column : str
        Column name to plot.
    bins : int or sequence
        Number of bins or explicit bin edges.
    title : str, optional
        Chart title.
    """
    pop_values = population_df[pop_column].dropna()
    failed_values = failed_df[failed_column].dropna()

    # Compute shared bin edges from the combined range
    all_values = np.concatenate([pop_values.values, failed_values.values])
    bin_edges = np.histogram_bin_edges(all_values, bins=bins)
    bin_size = bin_edges[1] - bin_edges[0]

    fig = go.Figure()

    fig.add_trace(go.Histogram(
        x=pop_values,
        xbins=dict(start=bin_edges[0], end=bin_edges[-1], size=bin_size),
        name="Population",
        marker_color="steelblue",
        opacity=0.6,
        yaxis="y1",
    ))

    fig.add_trace(go.Histogram(
        x=failed_values,
        xbins=dict(start=bin_edges[0], end=bin_edges[-1], size=bin_size),
        name="Failed",
        marker_color="firebrick",
        opacity=0.7,
        yaxis="y2",
    ))

    fig.update_layout(
        title=title or f"Distribution of {pop_column}",
        xaxis=dict(title=pop_column),
        yaxis=dict(title="Population count", title_font=dict(color="steelblue")),
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
