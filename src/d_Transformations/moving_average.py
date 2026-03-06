import pandas as pd


def take_moving_average(df: pd.DataFrame, num_years: int, min_periods: int = None) -> pd.DataFrame:
    """
    Computes a rolling moving average over year columns for a dataframe in financials_schema format.

    Args:
        df: DataFrame adhering to financials_schema (MultiIndex: Organization, Measure; columns are 4-digit year strings).
        num_years: Window size for the rolling average.
        min_periods: Minimum number of non-NaN observations required to produce a value.
                     Defaults to num_years (i.e., no partial windows).

    Returns:
        DataFrame in financials_schema format where each year column contains the
        moving average ending on that year.
    """
    if min_periods is None:
        min_periods = num_years

    year_cols = sorted([c for c in df.columns if str(c).isdigit()], key=lambda x: int(x))
    year_data = df[year_cols].T  # shape: (years, org*measure)

    rolled = year_data.rolling(window=num_years, min_periods=min_periods).mean()

    result = df.copy()
    result[year_cols] = rolled.T
    return result
