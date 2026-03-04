import os
import re
import pandas as pd


MA_FINANCIALS_DIR = os.path.join("src", "z_Data", "Raw_Data", "MA Financials")

# Metadata columns that are not financial measures
_METADATA_COLS = {
    'Org ID', 'Organization Name', 'Organization Type', 'HHS Org ID',
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
    (Org ID, Organization Name, Measure) with a single column for the given year.

    Args:
        df: Raw DataFrame from ingest_single_csv.
        year: The fiscal year represented by this file.

    Returns:
        DataFrame with MultiIndex (Org ID, Organization Name, Measure) and
        one column named <year>.
    """
    measure_cols = [c for c in df.columns if c not in _METADATA_COLS]
    id_cols = ['Org ID', 'Organization Name']

    df_long = df[id_cols + measure_cols].melt(
        id_vars=id_cols,
        var_name='Measure',
        value_name=year,
    )
    df_long['Measure'] = df_long['Measure'].str.strip()
    return df_long.set_index(['Org ID', 'Organization Name', 'Measure'])


def _extract_year(filename: str) -> int:
    match = re.search(r'(\d{4})', filename)
    if not match:
        raise ValueError(f"Could not extract year from filename: {filename}")
    return int(match.group(1))


def create_combined_ma_financial_df(directory: str = MA_FINANCIALS_DIR) -> pd.DataFrame:
    """
    Ingests all MA financials CSVs in directory, transposes each to
    (Org ID, Organization Name, Measure) x year format, and merges across
    years into a single DataFrame.

    Args:
        directory: Path to directory containing MA financials CSVs.

    Returns:
        DataFrame with MultiIndex (Org ID, Organization Name, Measure) and
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
        df_transposed = transpose_to_hospital_measure(df_raw, year)
        dfs.append(df_transposed)

    combined = pd.concat(dfs, axis=1)
    combined = combined[sorted(combined.columns)]
    return combined
