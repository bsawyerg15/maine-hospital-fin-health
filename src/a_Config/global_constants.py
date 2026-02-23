import os
import pandas as pd

class GlobalConstants:
    """
    Global constants for mappings, loaded once at class definition time.
    """
    MAPPINGS_DIR = os.path.dirname(__file__)
    
    HOSPITAL_MAPPINGS: dict[str, str] = pd.read_csv(
        os.path.join(MAPPINGS_DIR, 'hospital_name_mappings.csv')
    ).set_index('As Reported')['Standardized'].to_dict()
    
    MEASURE_MAPPINGS: dict[str, str] = pd.read_csv(
        os.path.join(MAPPINGS_DIR, 'clean_measure_names.csv')
    ).set_index('As Reported')['Standardized'].to_dict()

    MEASURE_HIERAERCHY_RENAMES: dict[str, str] = pd.read_csv(
        os.path.join(MAPPINGS_DIR, 'reported_measure_hierarchy_renames.csv')
    ).set_index(['Measure Name', 'Parent'])['New Name'].to_dict()
