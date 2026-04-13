import pandas as pd
import xarray as xr
import streamlit as st
from a_Config.enumerations.state_enum import State
from a_Config.global_constants import VALID_MEASURES, HOSPITAL_METADATA
from b_Ingest.z_get_financials_by_state import get_financials_by_state
from c_Fin_Statement_Processing.a_external_to_internal_mapping import apply_external_mappings
from c_Fin_Statement_Processing.c_add_imputed_sum_of_children_rows import add_imputed_sum_of_children_rows
from c_Fin_Statement_Processing.d_impute_systems_from_hospitals import impute_systems_from_hospitals


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

    #######################################################################################################
    # Internal Domain
    #######################################################################################################

    internal_domain_no_imputation_df = drop_non_model_measures(df)

    internal_domain_imputation_within_entity_df = add_imputed_sum_of_children_rows(internal_domain_no_imputation_df)

    internal_domain_df = impute_systems_from_hospitals(internal_domain_imputation_within_entity_df, state)

    #######################################################################################################
    # Augment with Metadata
    #######################################################################################################
    
    internal_domain_df['State'] = state
    internal_domain_df = internal_domain_df.set_index('State', append=True).reorder_levels(
        ['Organization', 'State', 'Measure', 'Year']
    )

    _year_failed = (
        internal_domain_df.index.droplevel(['Measure', 'Year'])
        .map(HOSPITAL_METADATA['Year Failed'])
    )
    internal_domain_df['Year Failed'] = _year_failed.map(
        lambda x: str(int(x)) if pd.notna(x) else None
    )

    return internal_domain_df


@st.cache_data
def _load_all_states(states: tuple) -> xr.Dataset:
    df = pd.concat([process_state_input_df(s) for s in states])
    df = df.rename_axis(
        index={'Organization': 'organization', 'State': 'state',
               'Measure': 'measure', 'Year': 'year'}
    )
    value_da = df['Value'].to_xarray().sortby('year')
    year_failed_da = (
        df['Year Failed']
        .groupby(level=['organization', 'state']).first()
        .to_xarray()
    )
    return xr.Dataset({'value': value_da}, coords={'year_failed': year_failed_da})


def load_pre_transformed_dataset(
    # Splitting from load_all_states for performace benefits
    states: list[State],
    entities=None,
    year_start=None,
    year_end=None,
) -> xr.Dataset:
    ds = _load_all_states(tuple(states))

    if entities is not None:
        ds = ds.sel(organization=list(entities))
    if year_start is not None and year_end is not None:
        ds = ds.sel(year=slice(str(year_start), str(year_end)))

    return ds
