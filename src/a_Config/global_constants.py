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
        os.path.join(MAPPINGS_DIR, 'measure_name_mappings.csv')
    ).set_index('As Reported')['Standardized'].to_dict()
