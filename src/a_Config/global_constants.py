import os
import pandas as pd
from typing import Dict

from a_Config.fin_statement_model_utils import (
    FINANCIAL_STATEMENT_MODEL,
    VALID_MEASURES,
    LINE_ITEMS,
)

MAPPINGS_DIR = os.path.join(os.path.dirname(__file__), 'csv_configs')

ORG_MAPPINGS_ME: Dict[str, str] = pd.read_csv(
    os.path.join(MAPPINGS_DIR, 'hospital_renames_me.csv')
).set_index('As Reported')['Standardized'].to_dict()

MEASURE_MAPPINGS: Dict[str, Dict[str, str]] = (
    pd.read_csv(os.path.join(MAPPINGS_DIR, 'clean_measure_names.csv'))
    .groupby('State')
    .apply(lambda g: g.set_index('As Reported')['Standardized'].to_dict())
    .to_dict()
)

MEASURE_HIERARCHY_RENAMES: Dict[tuple[str, str], str] = pd.read_csv(
    os.path.join(MAPPINGS_DIR, 'reported_measure_hierarchy_renames.csv')
).set_index(['Measure Name', 'Parent'])['New Name'].to_dict()

HOSPITAL_RENAMES_MA: Dict[tuple[str, int], str] = pd.read_csv(
    os.path.join(MAPPINGS_DIR, 'hospital_renames_ma.csv')
).set_index(['Organization', 'Org ID'])['New Organization'].to_dict()

EXTERNAL_MAPPINGS: pd.DataFrame = pd.read_csv(
    os.path.join(MAPPINGS_DIR, 'external_mappings.csv')
)

DERIVE_RATIOS: pd.DataFrame = pd.read_csv(
    os.path.join(MAPPINGS_DIR, 'derive_ratios.csv')
)
DERIVE_RATIOS['Multiplier'] = DERIVE_RATIOS['Multiplier'].fillna(1.0).astype(float)

HOSPITAL_METADATA: pd.DataFrame = pd.read_csv(
    os.path.join(MAPPINGS_DIR, 'hospital_metadata.csv')
).set_index(['Organization', 'State'])