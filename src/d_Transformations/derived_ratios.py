import pandas as pd
from a_Config.global_constants import DERIVE_RATIOS


def derive_ratios(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derives ratio measures from a financials dataframe using the DERIVE_RATIOS config.

    For each ratio, computes (sum of numerator components * multipliers) / (sum of denominator
    components * multipliers). A result is only included for a given organization and year if
    all component measures are present (non-NaN).

    Args:
        df: DataFrame with (Organization, State, Measure) MultiIndex, year columns, and
            metadata columns (Endpoint or MA, Raw or Derived, Year Failed).

    Returns:
        DataFrame in the same schema with derived ratio rows. Metadata columns are set to
        'Endpoint', 'Derived', and the Year Failed inferred per (Organization, State) from the input.
    """
    year_cols = [c for c in df.columns if str(c).isdigit()]
    available_measures = set(df.index.get_level_values('Measure'))
    results = []

    for ratio_name, group in DERIVE_RATIOS.groupby('Measure'):
        if not all(m in available_measures for m in group['Sub-Measure']):
            continue

        def weighted_sum(sub_group):
            parts = [
                df.xs(row['Sub-Measure'], level='Measure')[year_cols] * row['Multiplier']
                for _, row in sub_group.iterrows()
            ]
            # min_count=len(parts) ensures the sum is NaN for a given org/year
            # if any component is missing.
            return pd.concat(parts).groupby(level=[0, 1]).sum(min_count=len(parts))

        num = weighted_sum(group[group['Numerator or Denominator'] == 'Numerator'])
        den = weighted_sum(group[group['Numerator or Denominator'] == 'Denominator'])

        ratio = num / den
        ratio.index = pd.MultiIndex.from_tuples(
            [(org, state, ratio_name) for org, state in ratio.index],
            names=['Organization', 'State', 'Measure']
        )
        results.append(ratio)

    if not results:
        return pd.DataFrame()

    derived_df = pd.concat(results)
    org_state_to_year_failed = df['Year Failed'].groupby(level=['Organization', 'State']).first()
    derived_df.insert(0, 'Year Failed', derived_df.index.droplevel('Measure').map(org_state_to_year_failed))
    derived_df['Endpoint or MA'] = 'Endpoint'
    derived_df['Raw or Derived'] = 'Derived'
    derived_df = derived_df.set_index(['Endpoint or MA', 'Raw or Derived'], append=True)

    return derived_df
