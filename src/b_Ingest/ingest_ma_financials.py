import os
import re
import pandas as pd


MA_FINANCIALS_DIR = os.path.join("src", "z_Data", "Raw_Data", "MA Financials")

# Metadata columns that are not financial measures
_METADATA_COLS = {
    'Org ID', 'Organization Name', 'Organization', 'Organization Type', 'HHS Org ID',
    'Submission Period Year', 'Year Ending \nDate', 'Org Quarter',
    'Number Of Months', 'Quarter Range', 'Days in Period',
}


def ingest_single_csv(file_path: str) -> pd.DataFrame:
    """
    Reads a single MA financials CSV as-is.

    Args:
        file_path: Path to the CSV file.

    Returns:
        Raw DataFrame with all columns intact.
    """
    return pd.read_csv(file_path, encoding='utf-8-sig')


def transpose_to_hospital_measure(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """
    Transposes a wide MA financials DataFrame to long format keyed on
    (Organization, Measure) with a single column for the given year.

    Args:
        df: DataFrame from apply_and_validate_org_renames.
        year: The fiscal year represented by this file.

    Returns:
        DataFrame with MultiIndex (Organization, Measure) and one column named <year>.
    """
    measure_cols = [c for c in df.columns if c not in _METADATA_COLS]
    id_cols = ['Organization']

    df_long = df[id_cols + measure_cols].melt(
        id_vars=id_cols,
        var_name='Measure',
        value_name=str(year),
    )
    df_long['Measure'] = df_long['Measure'].str.strip()
    return df_long.set_index(['Organization', 'Measure'])


def _extract_year(filename: str) -> int:
    match = re.search(r'(\d{4})', filename)
    if not match:
        raise ValueError(f"Could not extract year from filename: {filename}")
    return int(match.group(1))


def _parse_dollar_value(val) -> float:
    if pd.isna(val):
        return float('nan')
    s = str(val).strip()
    negative = s.startswith('(') and s.endswith(')')
    if negative:
        s = s[1:-1]
    s = s.replace('$', '').replace(',', '').replace('%', '')
    try:
        result = float(s)
        return -result if negative else result
    except ValueError:
        return float('nan')


def parse_ma_numeric_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts dollar-formatted string values to floats.
    Handles: "$1,234,567" → 1234567.0, "($1,234,567)" → -1234567.0.
    Non-parseable values (ratios, percentages, etc.) become NaN.

    Args:
        df: DataFrame with MultiIndex (Organization, Measure)
            and year integer columns containing raw string values.

    Returns:
        DataFrame with the same structure and float values.
    """
    return df.apply(lambda col: col.map(_parse_dollar_value))


def clean_ma_measure_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies 1-to-1 measure name cleaning defined in clean_measure_names.csv (MA rows),
    via MEASURE_MAPPINGS in global_constants. Measures with no mapping are left unchanged.

    Args:
        df: DataFrame with MultiIndex (Organization, Measure).

    Returns:
        DataFrame with cleaned measure names in the Measure level.
    """
    from a_Config.global_constants import MEASURE_MAPPINGS

    new_measures = df.index.get_level_values('Measure').map(
        lambda x: MEASURE_MAPPINGS.get(x, x)
    )
    df.index = pd.MultiIndex.from_arrays(
        [
            df.index.get_level_values('Organization'),
            new_measures,
        ],
        names=df.index.names,
    )
    return df


def apply_and_validate_org_renames(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies MA organization name renames from hospital_renames_ma.csv keyed on
    (Organization Name, Org ID), then verifies that all organization names are
    unique within the DataFrame. Drops Org ID and renames the column to 'Organization'.

    Args:
        df: Raw DataFrame from ingest_single_csv.

    Returns:
        DataFrame with 'Organization' column (renamed and deduplicated) and Org ID removed.

    Raises:
        ValueError: If organization names are not unique after renaming.
    """
    from a_Config.global_constants import HOSPITAL_RENAMES_MA

    df = df.copy()
    df['Organization Name'] = df.apply(
        lambda row: HOSPITAL_RENAMES_MA.get(
            (row['Organization Name'], row['Org ID']), row['Organization Name']
        ),
        axis=1,
    )

    duplicates = df[df.duplicated('Organization Name', keep=False)]['Organization Name'].unique()
    if len(duplicates) > 0:
        raise ValueError(
            f"Organization names are not unique after renaming: {list(duplicates)}"
        )

    return df.drop(columns=['Org ID']).rename(columns={'Organization Name': 'Organization'})


def create_combined_ma_financial_df(directory: str = MA_FINANCIALS_DIR) -> pd.DataFrame:
    """
    Ingests all MA financials CSVs in directory, transposes each to
    (Org ID, Organization Name, Measure) x year format, and merges across
    years into a single DataFrame.

    Args:
        directory: Path to directory containing MA financials CSVs.

    Returns:
        DataFrame with MultiIndex (Organization, Measure) and
        one column per year, sorted chronologically.
    """
    csv_files = sorted(f for f in os.listdir(directory) if f.endswith('.csv'))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in: {directory}")

    dfs = []
    for filename in csv_files:
        year = _extract_year(filename)
        file_path = os.path.join(directory, filename)
        df_raw = ingest_single_csv(file_path)
        df_raw = apply_and_validate_org_renames(df_raw)
        df_transposed = transpose_to_hospital_measure(df_raw, year)
        dfs.append(df_transposed)

    combined = pd.concat(dfs, axis=1)
    combined = combined[sorted(combined.columns)]
    return combined
