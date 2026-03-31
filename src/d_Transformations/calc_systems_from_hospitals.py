import pandas as pd
from a_Config.global_constants import HOSPITAL_METADATA, SYSTEMS_TO_HOSPITALS_MAP, LINE_ITEMS


def calc_systems_from_hospitals(df: pd.DataFrame, state: str) -> pd.DataFrame:
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
        if not hospitals.issubset(hospitals_in_df):
            continue

        df_members = df_hospitals[
            df_hospitals.index.get_level_values('Organization').isin(hospitals)
        ]

        grouped = df_members.groupby(level=['Measure', 'Year'])
        counts = grouped['Value'].count()
        sums = grouped['Value'].sum(min_count=1)
        sums = sums.where(counts == len(hospitals))

        new_rows = sums.rename('Value').reset_index()
        new_rows['Organization'] = system
        new_rows = new_rows.set_index(['Organization', 'Measure', 'Year'])[['Value']]
        system_rows.append(new_rows)

    if not system_rows:
        return df

    all_system_rows = pd.concat(system_rows)
    return df.combine_first(all_system_rows)
