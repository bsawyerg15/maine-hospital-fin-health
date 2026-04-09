import pandas as pd
from .b_calculate_children_sums import calculate_children_sums

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
