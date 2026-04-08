import os
import pandas as pd
from a_Config.enumerations.state_enum import State
from b_Ingest.ingest_me_financials import create_combined_me_financial_df
from b_Ingest.ingest_ma_financials import create_combined_ma_financial_df, MA_FINANCIALS_DIR


_ME_DIR = os.path.join("src", "z_Data", "Preprocessed_Data")
_ME_HOSPITAL_FILES = [
    "hospital_dollar_elements_2005_2009.csv",
    "hospital_dollar_elements_2010_2014.csv",
    "hospital_dollar_elements_2015_2019.csv",
    "hospital_dollar_elements_2020_2024.csv",
    "hospital_ratios_2005_2009.csv",
    "hospital_ratios_2010_2014.csv",
    "hospital_ratios_2015_2019.csv",
    "hospital_ratios_2020_2024.csv"
]
_ME_HEALTH_SYSTEMS_FILES = [
    "health_systems_dollar_elements_2020_2024.csv"
]
_ME_FILES = _ME_HOSPITAL_FILES + _ME_HEALTH_SYSTEMS_FILES

_STATE_DISPATCH = {
    State.ME: lambda: create_combined_me_financial_df(_ME_DIR, _ME_FILES),
    State.MA: lambda: create_combined_ma_financial_df(MA_FINANCIALS_DIR),
}


def get_financials_by_state(state: State) -> pd.DataFrame:
    """
    Returns the combined financial DataFrame for the given state.

    Args:
        state: State enum member.

    Returns:
        Combined financial DataFrame with MultiIndex (Organization, Measure).

    Raises:
        ValueError: If the state is not supported.
    """
    if state not in _STATE_DISPATCH:
        raise ValueError(f"Unsupported state: '{state}'. Supported states: {list(_STATE_DISPATCH)}")
    return _STATE_DISPATCH[state]()


