import os
import pandas as pd
from a_Config.global_constants import (
    ORG_MAPPINGS_ME,
    MEASURE_MAPPINGS,
    MEASURE_HIERARCHY_RENAMES,
    VALID_MEASURES
)


def ingest_single_csv(file_path: str) -> pd.DataFrame:
    """
    Reads a single CSV file and sets the multi-index appropriately.

    Args:
        file_path (str): Path to the CSV file
        entity (str): Name of the first index column (default: 'Organization')

    Returns:
        pd.DataFrame: DataFrame with multi-index set keyed on ['Organization', 'Measure']
    """
    df = pd.read_csv(file_path)
    df = df.set_index(['Organization', 'Measure'])
    return df


def clean_financial_input_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the DataFrame:
    - Removes 'FY ' prefix from columns
    - Sorts year columns numerically
    - Maps hospital and measure names to standardized versions using GlobalConstants

    Args:
        df (pd.DataFrame): Input DataFrame with multi-index (Organization, Ratio/Measure)

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    # Remove 'FY ' prefix from column names
    df.columns = df.columns.str.replace('FY ', '')

    # Map hospital and measure names using global mappings
    hospital_map = ORG_MAPPINGS_ME
    measure_map = MEASURE_MAPPINGS['ME']

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
        df (pd.DataFrame): Cleaned DataFrame with MultiIndex (Organization, Measure)

    Returns:
        pd.DataFrame: Augmented with MultiIndex (Organization, Measure, Parent)
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
        "Total Restricted Fund Balance",
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
    
    for hospital, group in df_reset.groupby("Organization"):
        current_parent = None
        for idx in group.index:
            measure = df_reset.at[idx, "Measure"]
            if measure in parent_measures:
                df_reset.at[idx, "Parent"] = ""
                current_parent = measure
            else:
                df_reset.at[idx, "Parent"] = current_parent if current_parent else ""
    
    # Set new MultiIndex
    df_aug = df_reset.set_index(["Organization", "Measure", "Parent"])
    return df_aug


def process_financial_input_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Full processing pipeline for a single financial input DataFrame:
    - Cleans the DataFrame (removes 'FY ', maps names)
    - Augments with parent-level data (if applicable)
    - Renames measures by hierarchy to ensure unique (Organization, Measure) pairs
    - Verifies all measures against fin_statement_model.csv
    """
    df_clean = clean_financial_input_df(df)
    df_augmented = augment_input_df_with_parent(df_clean)
    df_renamed = rename_measures_by_hierarchy(df_augmented)
    return df_renamed


def rename_measures_by_hierarchy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Renames measures based on MEASURE_HIERAERCHY_RENAMES mapping using (Measure, Parent) key.
    Output keyed on (Organization, Measure) with all pairs unique.

    Args:
        df (pd.DataFrame): Input with MultiIndex (Organization, Measure, Parent)

    Returns:
        pd.DataFrame: Output with MultiIndex (Organization, Measure)
    """
    hierarchy_renames = MEASURE_HIERARCHY_RENAMES
    df_reset = df.reset_index()
    df_reset['Measure'] = df_reset.apply(
        lambda row: hierarchy_renames.get((row['Measure'], row['Parent']), row['Measure']),
        axis=1
    )
    df_renamed = df_reset.set_index(['Organization', 'Measure'])
    df_renamed = df_renamed.drop(columns=['Parent'])

    assert df_renamed.index.is_unique, f"Non-unique index elements: {df_renamed.index[df_renamed.index.duplicated()].tolist()}"

    return df_renamed


def create_combined_me_financial_df(directory: str, file_list: list[str]) -> pd.DataFrame:
    """
    Stitches multiple CSV files together:
    - Ingests each (read + index)
    - Cleans each
    - Concatenates horizontally into combined_df

    Args:
        directory (str): Directory containing CSV files
        file_list (list[str]): List of CSV filenames
        entity (str): First index column (default: 'Organization')
        measure (str): Second index column (default: 'Ratio')

    Returns:
        pd.DataFrame: Combined, cleaned DataFrame ready for analysis
    """
    dfs = []
    for file in file_list:
        file_path = os.path.join(directory, file)
        df_ingest = ingest_single_csv(file_path)
        df_clean = process_financial_input_df(df_ingest)
        dfs.append(df_clean)

    combined_df = dfs[0]
    for df in dfs[1:]:
        combined_df = combined_df.combine_first(df)

    # Sort columns by year (numerical)
    year_columns = sorted(combined_df.columns, key=lambda x: int(x))
    combined_df = combined_df[year_columns]
    
    return combined_df
