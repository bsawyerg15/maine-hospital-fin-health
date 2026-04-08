import pandas as pd
import xarray as xr
from a_Config.enumerations.state_enum import State
from a_Config.global_constants import VALID_MEASURES, HOSPITAL_METADATA
from b_Ingest.ingest_union import get_financials_by_state
from c_Processing.a_external_to_internal_mapping import apply_external_mappings
from c_Processing.b_sum_of_children import add_computed_parent_rows
from d_Transformations.calc_systems_from_hospitals import calc_systems_from_hospitals


def drop_non_model_measures(df: pd.DataFrame) -> pd.DataFrame:
    mask = df.index.get_level_values('Measure').isin(VALID_MEASURES)
    return df[mask]


def process_state_input_df(state: State, input_df=None) -> pd.DataFrame:
    """
    Runs the primary processing pipeline for one state.

    Returns:
        DataFrame with MultiIndex (Organization, State, Measure, Year)
        and columns Value, Year Failed.
    """
    if not input_df:
        input_df = get_financials_by_state(state)

    df = apply_external_mappings(input_df, state)
    df = drop_non_model_measures(df)
    df = add_computed_parent_rows(df)
    df = calc_systems_from_hospitals(df, state)

    df['State'] = state
    df = df.set_index('State', append=True).reorder_levels(
        ['Organization', 'State', 'Measure', 'Year']
    )

    _year_failed = (
        df.index.droplevel(['Measure', 'Year'])
        .map(HOSPITAL_METADATA['Year Failed'])
    )
    df['Year Failed'] = _year_failed.map(
        lambda x: str(int(x)) if pd.notna(x) else None
    )

    return df


def create_full_underived_df(states: list[State]) -> pd.DataFrame:
    """
    Processes all states and concatenates into a single DataFrame.

    Returns:
        DataFrame with MultiIndex (Organization, State, Measure, Year)
        and columns Value, Year Failed.
    """
    return pd.concat([process_state_input_df(s) for s in states])


def to_dataset(underived_df: pd.DataFrame) -> xr.Dataset:
    """
    Converts the processed underived pandas DataFrame to an xr.Dataset.

    Args:
        underived_df: Output of create_full_underived_df — MultiIndex
            (Organization, State, Measure, Year), columns Value, Year Failed.

    Returns:
        Dataset with a 'value' variable of shape
        (organization, state, measure, year) and a 'year_failed' coordinate
        of shape (organization, state).
    """
    df = underived_df.rename_axis(
        index={'Organization': 'organization', 'State': 'state',
               'Measure': 'measure', 'Year': 'year'}
    )

    value_da = df['Value'].to_xarray().sortby('year')

    year_failed_da = (
        df['Year Failed']
        .groupby(level=['organization', 'state']).first()
        .to_xarray()
    )

    return xr.Dataset(
        {'value': value_da},
        coords={'year_failed': year_failed_da},
    )
