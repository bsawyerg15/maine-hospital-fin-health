import pandas as pd
import numpy as np
from a_Config.global_constants import HOSPITAL_METADATA


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


def create_failed_hospital_df(df: pd.DataFrame, num_years=6) -> pd.DataFrame:
    """
    Takes a dataframe where the columns are yearly data. Filters down only to hospitals that have failed
    and returns dataframe in the form: Organization | Measure | ... T - 2 | T - 1 | T
    """

    failed_hospitals_metadata = HOSPITAL_METADATA[~HOSPITAL_METADATA['Year Failed'].isna()][['Year Failed']]

    year_cols = sorted([c for c in df.columns if str(c).isdigit()], key=lambda x: int(x))
    orgs_in_df = set(df.index.get_level_values('Organization'))

    result_dfs = []
    for hospital, row in failed_hospitals_metadata.iterrows():
        if hospital not in orgs_in_df:
            continue

        year_failed = int(row['Year Failed'])
        relevant_years = [y for y in year_cols if int(y) <= year_failed]
        num_missing_years_after = year_failed - int(relevant_years[-1])
        selected_years = relevant_years[-(num_years - num_missing_years_after):]

        if not selected_years:
            continue

        hospital_data = df.xs(hospital, level='Organization')[selected_years].copy()
        for i in range(num_missing_years_after):
            hospital_data[f'blank_{i}'] = np.nan

        first_anticipated_year = int(year_failed) - num_years + 1
        num_missing_years_before = int(selected_years[0]) - first_anticipated_year
        for i in range(num_missing_years_before):
            hospital_data.insert(0, f'before_{i}', np.nan)

        n = num_years
        hospital_data.columns = [
            'T' if i == n - 1 else f'T - {n - 1 - i}'
            for i in range(n)
        ]
        hospital_data.index = pd.MultiIndex.from_tuples(
            [(hospital, m) for m in hospital_data.index],
            names=['Organization', 'Measure']
        )
        result_dfs.append(hospital_data)

    if not result_dfs:
        return pd.DataFrame()
    return pd.concat(result_dfs)


def filter_to_non_failed_hospitals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filters out all hospitals that have failed.
    """
    failed_hospitals = set(HOSPITAL_METADATA[~HOSPITAL_METADATA['Year Failed'].isna()].index)
    orgs = df.index.get_level_values('Organization')
    return df[~orgs.isin(failed_hospitals)]
