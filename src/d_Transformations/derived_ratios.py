import pandas as pd
from a_Config.global_constants import DERIVE_RATIOS


def derive_ratios(dollar_df: pd.DataFrame) -> pd.DataFrame:
    """
    Derives ratio measures from a dollar-measure dataframe using the DERIVE_RATIOS config.

    For each ratio, computes (sum of numerator components * multipliers) / (sum of denominator
    components * multipliers). A result is only included for a given organization and year if
    all component measures are present (non-NaN).

    Args:
        dollar_df: DataFrame with (Organization, Measure) MultiIndex and year columns.

    Returns:
        DataFrame with the same structure containing the derived ratio rows.
    """
    year_cols = [c for c in dollar_df.columns if str(c).isdigit()]
    available_measures = set(dollar_df.index.get_level_values('Measure'))
    results = []

    for ratio_name, group in DERIVE_RATIOS.groupby('Measure'):
        if not all(m in available_measures for m in group['Sub-Measure']):
            continue

        def weighted_sum(sub_group):
            parts = [
                dollar_df.xs(row['Sub-Measure'], level='Measure')[year_cols] * row['Multiplier']
                for _, row in sub_group.iterrows()
            ]
            # min_count=len(parts) ensures the sum is NaN for a given org/year
            # if any component is missing.
            return pd.concat(parts).groupby(level=0).sum(min_count=len(parts))

        num = weighted_sum(group[group['Numerator or Denominator'] == 'Numerator'])
        den = weighted_sum(group[group['Numerator or Denominator'] == 'Denominator'])

        ratio = num / den
        ratio.index = pd.MultiIndex.from_tuples(
            [(org, ratio_name) for org in ratio.index],
            names=['Organization', 'Measure']
        )
        results.append(ratio)

    if not results:
        return pd.DataFrame()
    return pd.concat(results)
