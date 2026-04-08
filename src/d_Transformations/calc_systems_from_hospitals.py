import pandas as pd
from a_Config.enumerations.state_enum import State
from a_Config.global_constants import HOSPITAL_METADATA, SYSTEMS_TO_HOSPITALS_MAP, LINE_ITEMS


def calc_systems_from_hospitals(df: pd.DataFrame, state: State) -> pd.DataFrame:
    """
    Adds health-system-level line item aggregates to a per-state hospital DataFrame.

    For each health system in SYSTEMS_TO_HOSPITALS_MAP for this state, sums
    LINE_ITEMS measures across all member hospitals per measure/year.  A system
    is only included when every one of its member hospitals is present in the
    DataFrame as an organization.  For a given measure/year, if any member
    hospital has a missing value the aggregate is NaN.  Existing rows in the
    DataFrame take precedence over computed system rows.

    Args:
        df: DataFrame with MultiIndex (Organization, Measure, Year) and a
            'Value' column.  Expected to be the output of add_computed_parent_rows
            for a single state.
        state: The state being processed, used to look up the relevant systems
            in SYSTEMS_TO_HOSPITALS_MAP.

    Returns:
        DataFrame augmented with system-level rows for any (system, measure, year)
        not already present.
    """
    hospital_orgs = set(HOSPITAL_METADATA.index.get_level_values('Organization'))
    hospitals_in_df = set(df.index.get_level_values('Organization')) & hospital_orgs

    mask = (
        df.index.get_level_values('Organization').isin(hospitals_in_df)
        & df.index.get_level_values('Measure').isin(LINE_ITEMS)
    )
    df_hospitals = df[mask]

    system_rows = []
    for (system, sys_state), hospitals in SYSTEMS_TO_HOSPITALS_MAP.items():
        if sys_state != state:
            continue

        is_non_affiliated = system == 'Non-Affiliated'
        present_hospitals = hospitals & hospitals_in_df
        if not is_non_affiliated and not hospitals.issubset(hospitals_in_df):
            continue
        if is_non_affiliated and not present_hospitals:
            continue

        df_members = df_hospitals[
            df_hospitals.index.get_level_values('Organization').isin(
                present_hospitals if is_non_affiliated else hospitals
            )
        ]

        grouped = df_members.groupby(level=['Measure', 'Year'])
        sums = grouped['Value'].sum(min_count=1)

        new_rows = sums.rename('Value').reset_index()
        new_rows['Organization'] = system
        new_rows = new_rows.set_index(['Organization', 'Measure', 'Year'])[['Value']]
        system_rows.append(new_rows)

    if not system_rows:
        return df

    all_system_rows = pd.concat(system_rows)
    return df.combine_first(all_system_rows)
