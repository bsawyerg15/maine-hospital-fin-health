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

    # Group by Organization and Parent, sum across all children per year column
    year_cols = df.columns[df.columns.str.match(r'^\d{4}$')]
    group_cols = ['Organization', 'Parent']

    df_with_parent[year_cols] *= df_with_parent['Neg_Multiplier'].values[:, None]  # Apply negation if needed

    df_with_parent_group = df_with_parent.groupby(group_cols)

    # Non-NaN children present in data per group per year
    actual_counts = df_with_parent_group[year_cols].count()

    sums_df = df_with_parent_group[year_cols].sum(min_count=1)

    # Where the data doesn't have all model-defined children with values, return NaN
    all_present = actual_counts.eq(expected_children_per_parent, axis=0)
    sums_df = sums_df.where(all_present)

    sums_df.index.names = ['Organization', 'Measure']  # Rename Parent to Measure for consistency
    
    return sums_df


def add_computed_parent_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes the sum of children for each parent measure via calculate_children_sums,
    then inserts any parent rows that are present in the computed sums but absent
    from the input dataframe. Existing rows are left unchanged.

    Recursively repeats until no new rows can be computed, allowing multi-level
    parent hierarchies to be fully resolved.

    Args:
        df: DataFrame with MultiIndex (Organization, Measure) and numeric year columns.

    Returns:
        DataFrame augmented with computed rows for any parent measures not already present.
    """
    children_sums = calculate_children_sums(df)
    children_sums.dropna(axis=0, how='all', inplace=True)
    new_rows = children_sums[~children_sums.index.isin(df.index)]
    if new_rows.empty:
        return df
    augmented_df = pd.concat([df, new_rows])
    return add_computed_parent_rows(augmented_df) # TODO: somewhat inefficient because it recalcs on the whole dataframe, not just the siblings of new rows which is all that might have changed


def calculate_residuals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate residuals for parent line items: children_sum - parent_base_value.
    
    Args:
        df: Same input as calculate_children_sums.
    
    Returns:
        pd.DataFrame with MultiIndex (Organization, Measure) containing residuals for parent
        measures. NaNs filled with 0.
    """
    children_sums = calculate_children_sums(df)
    residuals = children_sums.sub(df).fillna(0)
    return residuals

