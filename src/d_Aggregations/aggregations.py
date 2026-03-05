import pandas as pd


def create_mean_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Takes a dataframe where the columns are yearly data. Returns the mean for each year 
    and adds a 'Total' column for the full-sample mean.
    Input:
        df: Adheres to financials_schema
    Returns:
        pd.
    """
    mean_df = df.groupby(level='Measure').mean()
    mean_df['Total'] = mean_df.stack().groupby(level='Measure').mean()
    return mean_df