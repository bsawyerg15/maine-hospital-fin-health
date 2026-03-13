import pandas as pd
from a_Config.global_constants import EXTERNAL_MAPPINGS


def apply_external_mappings(df: pd.DataFrame, state: str) -> pd.DataFrame:
    """
    Aggregates external (as-reported) measures into standardized measures
    by summing all external measures that share the same standardized target,
    as defined in external_mappings.csv for the given state.

    All original rows are preserved. For each standardized target, a new
    aggregated row is appended as the sum of the mapped external measures.
    Rows not referenced in the config are passed through unchanged.

    Args:
        df: DataFrame with MultiIndex (Org ID, Organization Name, Measure)
            and numeric year columns.
        state: State code to filter mappings (e.g. "MA").

    Returns:
        DataFrame with the same structure, with aggregated rows replacing
        the source external measure rows.
    """
    state_mappings = EXTERNAL_MAPPINGS[EXTERNAL_MAPPINGS['State'] == state]
    if state_mappings.empty:
        return df

    ext_to_std = state_mappings.set_index('External Measure')['Standardized Measure'].to_dict()

    measures_in_df = set(df.index.get_level_values('Measure'))
    relevant_ext = {k: v for k, v in ext_to_std.items() if k in measures_in_df}
    if not relevant_ext:
        return df

    # If an aggregation target already exists in the df but wasn't listed as
    # an external source, the concat would silently create duplicates. Fail loudly.
    std_targets = set(relevant_ext.values())
    implicit_conflicts = (std_targets & measures_in_df) - set(relevant_ext.keys())
    if implicit_conflicts:
        raise ValueError(
            f"Aggregation target(s) {sorted(implicit_conflicts)} already exist in the "
            f"dataframe but are not listed as external sources in external_mappings.csv "
            f"for state '{state}'. Add them explicitly so the intent is clear."
        )

    ext_mask = df.index.get_level_values('Measure').isin(relevant_ext)
    df_to_agg = df[ext_mask].copy()
    df_remaining = df

    new_measures = df_to_agg.index.get_level_values('Measure').map(relevant_ext)
    df_to_agg.index = pd.MultiIndex.from_arrays(
        [
            df_to_agg.index.get_level_values('Organization'),
            new_measures,
            df_to_agg.index.get_level_values('Year'),
        ],
        names=df_to_agg.index.names,
    )

    df_aggregated = df_to_agg.groupby(level=df_to_agg.index.names).sum(min_count=1)

    return pd.concat([df_remaining, df_aggregated])
