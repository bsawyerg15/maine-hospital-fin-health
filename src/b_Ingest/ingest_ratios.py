import os
import pandas as pd
from a_Config.global_constants import GlobalConstants


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


def clean_financial_input_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the DataFrame:
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

    return df


def augment_input_df_with_parent(df: pd.DataFrame) -> pd.DataFrame:
    """
    Augments the input DataFrame with a 'Parent' level in the MultiIndex.
    Scans rows in scraped order (preserved), assigns parent metadata based on hardcoded parents.
    
    Args:
        df (pd.DataFrame): Cleaned DataFrame with MultiIndex (Hospital, Measure)
    
    Returns:
        pd.DataFrame: Augmented with MultiIndex (Hospital, Measure, Parent)
    """
    parent_measures = [
        "Total Current Assets",
        "Total Non-Current Assets",
        "Total Unrestricted Assets",
        "Total Current Liabilities",
        "Total Non-Current Liabilities",
        "Fund Balance Unrestricted",
        "Total Liabilities and Equity",
        "Total Restricted Assets",
        "Total Restricted Liabilities and Equity",
        "Total Gross Patient Service Revenue",
        "Total Operating Revenue",
        "Total Operating Expenses",
        "Net Operating Income",
        "Total Non-Operating Revenue",
        "Excess of Revenue Over Expenses",
        "Total Surplus/Deficit",
        "Total Change in Unrestricted Net Assets"
    ]
    
    df_reset = df.reset_index()
    df_reset["Parent"] = ""
    
    for hospital, group in df_reset.groupby("Hospital"):
        current_parent = None
        for idx in group.index:
            measure = df_reset.at[idx, "Measure"]
            if measure in parent_measures:
                df_reset.at[idx, "Parent"] = ""
                current_parent = measure
            else:
                df_reset.at[idx, "Parent"] = current_parent if current_parent else ""
    
    # Set new MultiIndex
    df_aug = df_reset.set_index(["Hospital", "Measure", "Parent"])
    return df_aug


def process_financial_input_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Full processing pipeline for a single financial input DataFrame:
    - Cleans the DataFrame (removes 'FY ', maps names)
    - Augments with parent-level data (if applicable)
    - Renames measures by hierarchy to ensure unique (Hospital, Measure) pairs
    """
    df_clean = clean_financial_input_df(df)
    df_augmented = augment_input_df_with_parent(df_clean)
    df_renamed = rename_measures_by_hierarchy(df_augmented)
    return df_renamed


def rename_measures_by_hierarchy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Renames measures based on MEASURE_HIERAERCHY_RENAMES mapping using (Measure, Parent) key.
    Output keyed on (Hospital, Measure) with all pairs unique.

    Args:
        df (pd.DataFrame): Input with MultiIndex (Hospital, Measure, Parent)

    Returns:
        pd.DataFrame: Output with MultiIndex (Hospital, Measure)
    """
    hierarchy_renames = GlobalConstants.MEASURE_HIERAERCHY_RENAMES
    df_reset = df.reset_index()
    df_reset['Measure'] = df_reset.apply(
        lambda row: hierarchy_renames.get((row['Measure'], row['Parent']), row['Measure']),
        axis=1
    )
    df_renamed = df_reset.set_index(['Hospital', 'Measure']).drop(columns=['Parent'])

    assert df_renamed.index.is_unique, f"Non-unique index elements: {df_renamed.index[df_renamed.index.duplicated()].tolist()}"

    return df_renamed


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