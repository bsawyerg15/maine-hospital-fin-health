import re
import os
import pandas as pd
from enum import StrEnum


def _to_key(name: str) -> str:
    key = name.replace("'", "")
    key = re.sub(r'[^A-Za-z0-9]+', '_', key)
    return key.strip('_').upper()


_CSV_PATH = os.path.join(os.path.dirname(__file__), '..', 'csv_configs', 'hospital_metadata.csv')
_df = pd.read_csv(_CSV_PATH)

Hospital = StrEnum('Hospital', {_to_key(name): name for name in _df['Organization']})
HealthSystem = StrEnum('HealthSystem', {_to_key(name): name for name in _df['Healthcare System'].unique()})

Entity = Hospital | HealthSystem


def to_entity(name: str) -> Hospital | HealthSystem:
    try:
        return Hospital(name)
    except ValueError:
        pass
    try:
        return HealthSystem(name)
    except ValueError:
        pass
    raise ValueError(f"'{name}' is not a known Hospital or HealthSystem.")
