import os
import pandas as pd
from typing import Dict

from a_Config.enumerations.state_enum import State
from a_Config.enumerations.hospital_enum import Hospital, HealthSystem
from a_Config.fin_statement_model_utils import (
    FINANCIAL_STATEMENT_MODEL,
    VALID_MEASURES,
    LINE_ITEMS,
    ALL_RATIOS,
    BALANCE_SHEET_MEASURES,
    INCOME_STATEMENT_MEASURES,
    OTHER_MEASURES
)

#######################################################################################################
# Fin Statement Metadata
#######################################################################################################

MAPPINGS_DIR = os.path.join(os.path.dirname(__file__), 'csv_configs')

ORG_MAPPINGS_ME: Dict[str, str] = pd.read_csv(
    os.path.join(MAPPINGS_DIR, 'hospital_renames_me.csv')
).set_index('As Reported')['Standardized'].to_dict()

MEASURE_MAPPINGS: Dict[State, Dict[str, str]] = {
    State(state): mapping
    for state, mapping in (
        pd.read_csv(os.path.join(MAPPINGS_DIR, 'clean_measure_names.csv'))
        .groupby('State')
        .apply(lambda g: g.set_index('As Reported')['Standardized'].to_dict())
        .to_dict()
    ).items()
}

MEASURE_HIERARCHY_RENAMES: Dict[tuple[str, str], str] = pd.read_csv(
    os.path.join(MAPPINGS_DIR, 'reported_measure_hierarchy_renames.csv')
).set_index(['Measure Name', 'Parent'])['New Name'].to_dict()

HOSPITAL_RENAMES_MA: Dict[tuple[str, int], str] = pd.read_csv(
    os.path.join(MAPPINGS_DIR, 'hospital_renames_ma.csv')
).set_index(['Organization', 'Org ID'])['New Organization'].to_dict()

EXTERNAL_MAPPINGS: pd.DataFrame = pd.read_csv(
    os.path.join(MAPPINGS_DIR, 'external_mappings.csv'),
    converters={'State': State},
)

DERIVE_RATIOS: pd.DataFrame = pd.read_csv(
    os.path.join(MAPPINGS_DIR, 'derive_ratios.csv')
)
DERIVE_RATIOS['Multiplier'] = DERIVE_RATIOS['Multiplier'].fillna(1.0).astype(float)
DERIVE_RATIOS['Optional?'] = DERIVE_RATIOS['Optional?'].fillna(False).astype(bool)

#######################################################################################################
# Entity Metadata
#######################################################################################################

_hospital_metadata_raw: pd.DataFrame = pd.read_csv(
    os.path.join(MAPPINGS_DIR, 'hospital_metadata.csv')
).set_index(['Organization', 'State'])
_hospital_metadata_raw.index = _hospital_metadata_raw.index.set_levels(
    _hospital_metadata_raw.index.levels[0].map(Hospital), level=0
).set_levels(
    _hospital_metadata_raw.index.levels[1].map(State), level=1
)
HOSPITAL_METADATA: pd.DataFrame = _hospital_metadata_raw

def _build_systems_map() -> Dict[tuple[HealthSystem, State], set[Hospital]]:
    df = HOSPITAL_METADATA.reset_index()
    missing = df[df['Healthcare System'].isna()]['Organization'].tolist()
    if missing:
        raise ValueError(f"Organizations missing a Healthcare System: {missing}. If independent, label Non-Affiliated.")
    df['Healthcare System'] = df['Healthcare System'].map(HealthSystem)
    return df.groupby(['Healthcare System', 'State'])['Organization'].apply(set).to_dict()

SYSTEMS_TO_HOSPITALS_MAP: Dict[tuple[HealthSystem, State], set[Hospital]] = _build_systems_map()

#######################################################################################################
# Helper Functions
#######################################################################################################

def get_measure_tickformat(measure: str, is_pct: bool = False) -> str:
    """Return Plotly tickformat string for a measure based on fin_statement_model Format column.

    'Percent' measures (margins, returns) → '.1%'  (e.g. 0.05 → '5.0%')
    'Float' measures (ratios, days)        → '.1f'
    'Millions' measures (balance sheet)    → '$,.1f'  (e.g. 1234567 → '$1,234,567.0')
    Unknown measures default to '.1f'.
    """
    if is_pct:
        return '.1%'
    if measure in FINANCIAL_STATEMENT_MODEL.index:
        fmt = FINANCIAL_STATEMENT_MODEL.loc[measure, 'Format']
        match fmt:
            case 'Percent':
                return '.1%'
            case 'Millions':
                return '$,.1f'
            case _:
                return '.1f'
    return '.1f'