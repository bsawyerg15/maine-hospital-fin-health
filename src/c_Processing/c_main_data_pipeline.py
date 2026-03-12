import pandas as pd
from a_Config.global_constants import VALID_MEASURES, HOSPITAL_METADATA
from a_Config.financials_schema import financials_schema
from b_Ingest.ingest_union import get_financials_by_state
from c_Processing.a_external_to_internal_mapping import apply_external_mappings
from c_Processing.b_sum_of_children import add_computed_parent_rows


    
def verify_measures_against_model(df: pd.DataFrame) -> None:
    """
    Verifies that all measures in the input DataFrame index are present in GlobalConstants.VALID_MEASURES.
    
    Raises:
        ValueError: If invalid measures are found.
    """
    valid_measures = VALID_MEASURES
    input_measures = set(df.index.get_level_values('Measure').unique())
    invalid = input_measures - valid_measures
    if invalid:
        raise ValueError(f"Invalid measures found: {sorted(list(invalid))}")


def drop_non_model_measures(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drops rows from the DataFrame where the Measure index level is not in VALID_MEASURES.

    Args:
        df: DataFrame with a MultiIndex containing a 'Measure' level.

    Returns:
        pd.DataFrame: Filtered DataFrame containing only rows with valid measures.
    """
    mask = df.index.get_level_values('Measure').isin(VALID_MEASURES)
    return df[mask]


def process_state_input_df(state, input_df=None) -> pd.DataFrame:
    """
    Runs the primary processing pipeline for the financials. Runs the following steps:
    - Validates input dataframe adheres to index=[Organization, Measure], columns are string years.
    - Maps external definitions to internal
    - Checks that all remaining measures are within the model
    - Adds in model rows computed via sum of children

    Returns:
        pd.Dataframe: fully processed financials dataframe ready for analysis
    """

    if not input_df:
        input_df = get_financials_by_state(state)

    df_with_external_mapping = apply_external_mappings(input_df, state)
    drop_non_model_measures(df_with_external_mapping)
    # verify_measures_against_model(df_with_external_mapping)
    df_with_sum_of_children = add_computed_parent_rows(df_with_external_mapping)

    processed_df = df_with_sum_of_children

    processed_df['State'] = state
    processed_df = processed_df.set_index('State', append=True).reorder_levels(['Organization', 'State', 'Measure'])
    processed_df['Endpoint or MA'] = 'Endpoint'
    processed_df['Raw or Derived'] = 'Raw'
    processed_df = processed_df.set_index(['Endpoint or MA', 'Raw or Derived'], append=True)
    _year_failed = processed_df.index.droplevel(['Measure', 'Endpoint or MA', 'Raw or Derived']).map(HOSPITAL_METADATA['Year Failed'])
    processed_df['Year Failed'] = _year_failed.map(lambda x: str(int(x)) if pd.notna(x) else None)

    financials_schema.validate(processed_df) # validate that the input df conforms to the expected shape
    return processed_df


def create_full_underived_df(states: list) -> pd.DataFrame:
    """
    Outer loop for the initial processing pipeline. Takes in a list of states and returns the input dataframe
    for all states without any derivation or averages.
    """
    dfs = []
    for state in states:
        df = process_state_input_df(state)
        dfs.append(df)
    underived_df = pd.concat(dfs)

    return underived_df