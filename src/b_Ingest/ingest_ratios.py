import os
import pandas as pd
from src.a_Config.global_constants import GlobalConstants


def ingest_single_csv(file_path: str, entity: str = 'Hospital', measure: str = 'Ratio') -> pd.DataFrame:
    """
    Reads a single CSV file and sets the multi-index appropriately.

    Args:
        file_path (str): Path to the CSV file
        entity (str): Name of the first index column (default: 'Hospital')
        measure (str): Name of the second index column (default: 'Ratio')

    Returns:
        pd.DataFrame: DataFrame with multi-index set
    """
    df = pd.read_csv(file_path)
    df = df.set_index([entity, measure])
    return df


def process_financial_input_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Processes and cleans the DataFrame:
    - Removes 'FY ' prefix from columns
    - Sorts year columns numerically
    - Maps hospital and measure names to standardized versions using GlobalConstants

    Args:
        df (pd.DataFrame): Input DataFrame with multi-index (Hospital, Ratio/Measure)

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    # Remove 'FY ' prefix from column names
    df.columns = df.columns.str.replace('FY ', '')

    # Map hospital and measure names using global mappings
    hospital_map = GlobalConstants.HOSPITAL_MAPPINGS
    measure_map = GlobalConstants.MEASURE_MAPPINGS

    new_hospitals = df.index.get_level_values(0).map(lambda x: hospital_map.get(x, x))
    new_measures = df.index.get_level_values(1).map(lambda x: measure_map.get(x, x))

    df.index = pd.MultiIndex.from_arrays(
        [new_hospitals, new_measures],
        names=df.index.names
    )

    # Sort index for consistency
    df = df.sort_index()

    return df


def create_combined_financial_df(directory: str, file_list: list[str], entity: str = 'Hospital', measure: str = 'Ratio') -> pd.DataFrame:
    """
    Stitches multiple CSV files together:
    - Ingests each (read + index)
    - Cleans each
    - Concatenates horizontally into combined_df

    Args:
        directory (str): Directory containing CSV files
        file_list (list[str]): List of CSV filenames
        entity (str): First index column (default: 'Hospital')
        measure (str): Second index column (default: 'Ratio')

    Returns:
        pd.DataFrame: Combined, cleaned DataFrame ready for analysis
    """
    dfs = []
    for file in file_list:
        file_path = os.path.join(directory, file)
        df_ingest = ingest_single_csv(file_path, entity, measure)
        df_clean = process_financial_input_df(df_ingest)
        dfs.append(df_clean)

    combined_df = pd.concat(dfs, axis=1)

    # Sort columns by year (numerical)
    year_columns = sorted(combined_df.columns, key=lambda x: int(x))
    combined_df = combined_df[year_columns]
    
    return combined_df