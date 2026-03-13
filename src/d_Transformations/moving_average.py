import pandas as pd


def take_moving_average(df: pd.DataFrame, num_years: int, min_periods: int = None) -> pd.DataFrame:
    """
    Computes a rolling moving average over the Year index dimension.

    Args:
        df: DataFrame adhering to financials_schema (MultiIndex ending in Year; 'Value' and
            'Year Failed' columns).
        num_years: Window size for the rolling average.
        min_periods: Minimum number of non-NaN observations required to produce a value.
                     Defaults to num_years (i.e., no partial windows).

    Returns:
        DataFrame in financials_schema format where each Year row contains the
        moving average ending on that year.
    """
    if min_periods is None:
        min_periods = num_years

    non_year_levels = df.index.names[:-1]  # everything except 'Year'

    df_sorted = df.sort_index(level='Year')
    rolled_values = (
        df_sorted.groupby(level=non_year_levels)['Value']
        .transform(lambda s: s.rolling(window=num_years, min_periods=min_periods).mean())
    )

    result = df_sorted.copy()
    result['Value'] = rolled_values
    return result
