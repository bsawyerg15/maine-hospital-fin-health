import pandas as pd
from a_Config.global_constants import DERIVE_RATIOS


def derive_ratios(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derives ratio measures from a financials dataframe using the DERIVE_RATIOS config.

    For each ratio, computes (sum of numerator components * multipliers) / (sum of denominator
    components * multipliers). A result is only included for a given organization and year if
    all component measures are present (non-NaN).

    Args:
        df: DataFrame with (Organization, State, Measure, Endpoint or MA, Raw or Derived, Year)
            MultiIndex, a 'Value' column, and a 'Year Failed' metadata column.

    Returns:
        DataFrame in the same schema with derived ratio rows. Metadata columns are set to
        'Endpoint', 'Derived', and the Year Failed inferred per (Organization, State) from the input.
    """
    available_measures = set(df.index.get_level_values('Measure'))
    results = []

    for ratio_name, group in DERIVE_RATIOS.groupby('Measure'):
        if not all(m in available_measures for m in group['Sub-Measure']):
            continue

        def weighted_sum(sub_group):
            parts = [
                df.xs(row['Sub-Measure'], level='Measure')['Value'] * row['Multiplier']
                for _, row in sub_group.iterrows()
            ]
            # min_count=len(parts) ensures the sum is NaN for a given org/year
            # if any component is missing.
            return pd.concat(parts).groupby(level=['Organization', 'State', 'Year']).sum(min_count=len(parts))

        num = weighted_sum(group[group['Numerator or Denominator'] == 'Numerator'])
        den = weighted_sum(group[group['Numerator or Denominator'] == 'Denominator'])

        ratio = num / den
        ratio.index = pd.MultiIndex.from_tuples(
            [(org, state, ratio_name, 'Endpoint', 'Derived', year) for org, state, year in ratio.index],
            names=['Organization', 'State', 'Measure', 'Endpoint or MA', 'Raw or Derived', 'Year']
        )
        results.append(ratio)

    if not results:
        return pd.DataFrame()

    derived_df = pd.concat(results).rename('Value').to_frame()
    org_state_to_year_failed = df['Year Failed'].groupby(level=['Organization', 'State']).first()
    orgs = derived_df.index.get_level_values('Organization')
    states = derived_df.index.get_level_values('State')
    derived_df['Year Failed'] = pd.MultiIndex.from_arrays([orgs, states]).map(org_state_to_year_failed)

    return derived_df
