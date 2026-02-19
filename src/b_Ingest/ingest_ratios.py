import os
import pandas as pd

def ingest_financial_csvs(directory, file_list, entity='Hospital', measure='Measure'):
    """
    Reads multiple CSV files containing financial ratios from a specified directory,
    concatenates them into a single dataframe, sets the index to Hospital and Measure,
    and cleans up column names.

    Args:
        directory (str): Path to the directory containing the CSV files
        file_list (list): List of CSV file names in the directory
        entity (str): Name of the column to use as the first level of the index (default 'Hospital')
        measure (str): Name of the column to use as the second level of the index (default 'Measure')

    Returns:
        pd.DataFrame: Combined dataframe with Hospital and Ratio as multi-index,
                     year columns sorted in ascending order with 'FY' removed from names
    """
    dfs = []
    for file in file_list:
        file_path = os.path.join(directory, file)
        df = pd.read_csv(file_path)
        df = df.set_index([entity, measure])
        dfs.append(df)

    # Concatenate all dataframes horizontally
    combined_df = pd.concat(dfs, axis=1)

    # Remove 'FY ' prefix from column names
    combined_df.columns = combined_df.columns.str.replace('FY ', '')

    # Sort columns by year (numerical)
    year_columns = sorted(combined_df.columns, key=lambda x: int(x))
    combined_df = combined_df[year_columns]

    return combined_df
