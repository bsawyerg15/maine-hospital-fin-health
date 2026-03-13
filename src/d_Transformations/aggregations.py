import pandas as pd
import numpy as np
from a_Config.global_constants import HOSPITAL_METADATA


def create_mean_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Takes a dataframe where Year is an index level. Returns the mean Value for each
    (Measure, Year) combination and adds a 'Total' column for the full-sample mean.

    Args:
        df: Adheres to financials_schema
    Returns:
        DataFrame with Measure index and Year columns, plus a 'Total' column.
    """
    mean_df = df.groupby(level=['Measure', 'Year'])['Value'].mean().unstack('Year')
    mean_df['Total'] = df.groupby(level='Measure')['Value'].mean()
    return mean_df


def create_failed_hospital_df(df: pd.DataFrame, num_years=6) -> pd.DataFrame:
    """
    Filters down only to hospitals that have failed and returns a tall dataframe with
    a 'Relative Year' column indicating years relative to failure (0 = failure year,
    -1 = one year prior, etc.).

    Returns:
        DataFrame in financials_schema format (Year in index) filtered to failed hospitals
        within num_years of failure, with an added 'Relative Year' column.
    """
    failed_hospitals_metadata = HOSPITAL_METADATA[~HOSPITAL_METADATA['Year Failed'].isna()][['Year Failed']]

    orgs_in_df = set(df.index.get_level_values('Organization'))

    result_dfs = []
    for (hospital, state), row in failed_hospitals_metadata.iterrows():
        if hospital not in orgs_in_df:
            continue

        year_failed = int(row['Year Failed'])
        hospital_df = df.xs(hospital, level='Organization')
        all_years = sorted(hospital_df.index.get_level_values('Year').unique().astype(int))

        relevant_years = [y for y in all_years if y <= year_failed]
        if not relevant_years:
            continue

        selected_years = relevant_years[-(num_years):]

        if not selected_years:
            continue

        year_mask = hospital_df.index.get_level_values('Year').astype(int).isin(selected_years)
        hospital_data = hospital_df[year_mask].copy()
        hospital_data.index = pd.MultiIndex.from_tuples(
            [(hospital,) + m for m in hospital_data.index],
            names=['Organization'] + hospital_df.index.names
        )
        hospital_data['Relative Year'] = hospital_data.index.get_level_values('Year').astype(int) - year_failed
        result_dfs.append(hospital_data)

    if not result_dfs:
        return pd.DataFrame()
    return pd.concat(result_dfs)


def filter_to_non_failed_hospitals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filters out all hospitals that have failed.
    """
    failed_hospitals = set(HOSPITAL_METADATA[~HOSPITAL_METADATA['Year Failed'].isna()].index.get_level_values('Organization'))
    orgs = df.index.get_level_values('Organization')
    return df[~orgs.isin(failed_hospitals)]
