import pandas as pd
from a_Config.global_constants import FINANCIAL_STATEMENT_MODEL


def calculate_children_sums(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate the sum of direct children for each parent line item.
    
    Joins the input dataframe with FINANCIAL_STATEMENT_MODEL to get parent relationships,
    then groups by Hospital and Parent to sum children values per fiscal year.
    
    Args:
        df: DataFrame from create_combined_financial_df with MultiIndex (Hospital, Measure)
            and fiscal year columns containing values.
    
    Returns:
        pd.DataFrame with MultiIndex (Hospital, Parent) and fiscal year columns containing
        sums of direct children values. NaNs filled with 0.
    """
    # Reset index to make Hospital and Measure columns
    df_reset = df.reset_index()
    
    # Prepare model with Measure and Parent columns
    model_reset = FINANCIAL_STATEMENT_MODEL.reset_index()[['Measure', 'Parent', 'Neg_Multiplier']].copy()
    
    # Left join to add Parent to each row
    df_with_parent = df_reset.merge(
        model_reset,
        on='Measure',
        how='left'
    )
    
    # Drop rows where Parent is NaN or empty (top-level or orphans)
    df_with_parent = df_with_parent.dropna(subset=['Parent'])
    df_with_parent = df_with_parent[df_with_parent['Parent'] != '']
    
    # Group by Hospital and Parent, sum across all children per year column
    year_cols = df.columns[df.columns.str.match(r'^\d{4}$')]
    group_cols = ['Hospital', 'Parent']

    df_with_parent[year_cols] *= df_with_parent['Neg_Multiplier'].values[:, None]  # Apply negation if needed
    sums_df = df_with_parent.groupby(group_cols)[year_cols].sum()
    
    # Fill NaN with 0
    sums_df = sums_df.fillna(0)
    sums_df.index.names = ['Hospital', 'Measure']  # Rename Parent to Measure for consistency
    
    return sums_df


def add_computed_parent_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes the sum of children for each parent measure via calculate_children_sums,
    then inserts any parent rows that are present in the computed sums but absent
    from the input dataframe. Existing rows are left unchanged.

    Args:
        df: DataFrame with MultiIndex (Hospital, Measure) and numeric year columns.

    Returns:
        DataFrame augmented with computed rows for any parent measures not already present.
    """
    children_sums = calculate_children_sums(df)
    new_rows = children_sums[~children_sums.index.isin(df.index)]
    if new_rows.empty:
        return df
    return pd.concat([df, new_rows])


def calculate_residuals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate residuals for parent line items: children_sum - parent_base_value.
    
    Args:
        df: Same input as calculate_children_sums.
    
    Returns:
        pd.DataFrame with MultiIndex (Hospital, Measure) containing residuals for parent
        measures. NaNs filled with 0.
    """
    children_sums = calculate_children_sums(df)
    residuals = children_sums.sub(df).fillna(0)
    return residuals

