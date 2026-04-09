import pandas as pd
from a_Config.global_constants import FINANCIAL_STATEMENT_MODEL


def calculate_children_sums(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate the sum of direct children for each parent line item.
    
    Joins the input dataframe with FINANCIAL_STATEMENT_MODEL to get parent relationships,
    then groups by Organization and Parent to sum children values per fiscal year.

    Args:
        df: DataFrame from create_combined_financial_df with MultiIndex (Organization, Measure)
            and fiscal year columns containing values.

    Returns:
        pd.DataFrame with MultiIndex (Organization, Parent) and fiscal year columns containing
        sums of direct children values. NaNs filled with 0.
    """
    # Reset index to make Organization and Measure columns
    df_reset = df.reset_index()
    
    # Prepare model with Measure and Parent columns
    model_reset = FINANCIAL_STATEMENT_MODEL.reset_index()[['Measure', 'Parent', 'Neg_Multiplier']].copy()
    model_reset = model_reset.dropna(subset=['Parent'])
    model_reset = model_reset[model_reset['Parent'] != '']

    # Expected number of children per Parent according to the model
    expected_children_per_parent = model_reset.groupby('Parent')['Measure'].count()

    # Left join to add Parent to each row
    df_with_parent = df_reset.merge(
        model_reset,
        on='Measure',
        how='inner'  # only keep rows that have a parent in the model
    )

    # Group by Organization, Parent, and Year, sum across all children per group
    group_cols = ['Organization', 'Parent', 'Year']

    df_with_parent['Value'] *= df_with_parent['Neg_Multiplier']  # Apply negation if needed

    df_with_parent_group = df_with_parent.groupby(group_cols)

    # Non-NaN children present in data per group
    actual_counts = df_with_parent_group['Value'].count()

    sums_df = df_with_parent_group['Value'].sum(min_count=1)

    # Where the data doesn't have all model-defined children with values, return NaN
    expected = actual_counts.index.get_level_values('Parent').map(expected_children_per_parent)
    all_present = actual_counts == expected
    sums_df = sums_df.where(all_present)

    sums_df.index.names = ['Organization', 'Measure', 'Year']  # Rename Parent to Measure for consistency

    return sums_df.rename('Value').to_frame()