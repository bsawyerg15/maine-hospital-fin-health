import pandas as pd
from a_Config.financials_schema import financials_schema
from d_Transformations.derived_ratios import derive_ratios
from d_Transformations.moving_average import take_moving_average


def run_transformation_pipeline(underived_df: pd.DataFrame, ma_years) -> pd.DataFrame:
    """
    Runs the full transformation pipeline on an underived financials dataframe.

    Steps:
    1. Computes derived ratios and appends them as 'Derived' endpoint rows.
    2. Computes moving averages of all endpoint rows and appends them as 'MA' rows.

    Args:
        underived_df: DataFrame output from create_full_underived_df, with MultiIndex
                      (Organization, State, Measure), metadata columns (Endpoint or MA,
                      Raw or Derived, Year Failed), and year columns.
        ma_years: Window size for the rolling moving average.

    Returns:
        DataFrame combining raw endpoints, derived ratio endpoints, and moving average rows,
        validated against financials_schema.
    """
    # --- Step 1: Derive ratios ---
    derived_df = derive_ratios(underived_df)
    endpoint_df = pd.concat([underived_df, derived_df]) if not derived_df.empty else underived_df

    # --- Step 2: Moving average ---
    # take_moving_average copies the df and updates year cols; non-year cols carry over
    ma_df = take_moving_average(endpoint_df, ma_years)
    idx = ma_df.index.to_frame()
    idx['Endpoint or MA'] = 'MA'
    ma_df.index = pd.MultiIndex.from_frame(idx)

    result = pd.concat([endpoint_df, ma_df])
    financials_schema.validate(result)
    return result