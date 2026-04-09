import pandas as pd
from a_Config.global_constants import FINANCIAL_STATEMENT_MODEL
from .b_calculate_children_sums import calculate_children_sums


def add_imputed_sum_of_children_rows(df: pd.DataFrame) -> pd.DataFrame:
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
    return add_imputed_sum_of_children_rows(augmented_df) # TODO: somewhat inefficient because it recalcs on the whole dataframe, not just the siblings of new rows which is all that might have changed

