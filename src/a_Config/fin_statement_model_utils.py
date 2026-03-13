import os
import pandas as pd
from functools import lru_cache
from typing import Dict, Set

_MAPPINGS_DIR = os.path.join(os.path.dirname(__file__), 'csv_configs')

FINANCIAL_STATEMENT_MODEL: pd.DataFrame = pd.read_csv(
    os.path.join(_MAPPINGS_DIR, 'fin_statement_model.csv')
).set_index('Measure')

FINANCIAL_STATEMENT_MODEL['Negate?'] = FINANCIAL_STATEMENT_MODEL['Negate?'].astype(bool)
FINANCIAL_STATEMENT_MODEL['Neg_Multiplier'] = FINANCIAL_STATEMENT_MODEL['Negate?'].astype(int).replace({1: -1, 0: 1})


@lru_cache(maxsize=None)
def get_measure_paths() -> Dict[str, str]:
    """Lazy-computed hierarchical paths for all measures."""
    model = FINANCIAL_STATEMENT_MODEL
    paths: Dict[str, str] = {}
    def recurse(m: str) -> str:
        if m in paths:
            return paths[m]
        parent = model.loc[m, 'Parent']
        if pd.isna(parent) or str(parent).strip() == '':
            paths[m] = m
            return m
        parent_path = recurse(str(parent))
        paths[m] = f"{parent_path}/{m}"
        return paths[m]
    for measure in model.index:
        recurse(str(measure))
    return paths


def get_fin_statement_path(measure: str) -> str:
    """Get hierarchical path for a measure."""
    return get_measure_paths()[measure]


FINANCIAL_STATEMENT_MODEL['Path'] = FINANCIAL_STATEMENT_MODEL.index.map(get_fin_statement_path)


def get_fin_statement_descendants(measure: str) -> Set[str]:
    """Get all descendant measures of a given measure."""
    model = FINANCIAL_STATEMENT_MODEL
    descendants = set()
    def recurse(m):
        children_df = model.reset_index()
        children = children_df[children_df['Parent'] == m]['Measure'].str.strip().tolist()
        children = [c for c in children if c != m]
        descendants.update(children)
        for child in children:
            recurse(child)
    recurse(measure)
    return descendants


def get_fin_statement_descendants_and_self(measure: str) -> Set[str]:
    """Return descendants of a measure and the measure itself."""
    return {measure} | get_fin_statement_descendants(measure)


@lru_cache(maxsize=None)
def get_fin_statement_path2(measure: str) -> str:
    """Alternative hierarchical path impl (memoized, cycle-safe)."""
    model = FINANCIAL_STATEMENT_MODEL
    path_cache = {}
    def recurse(m):
        if m in path_cache:
            return path_cache[m]
        parent_row = model.reset_index()
        parent_idx = parent_row[parent_row['Measure'] == m]
        parent = parent_idx['Parent'].iloc[0] if not parent_idx.empty else ''
        if pd.isna(parent) or parent == '' or parent == m:
            path = m
        else:
            path = recurse(parent) + '/' + m
        path_cache[m] = path
        return path
    return recurse(measure)


@lru_cache(maxsize=None)
def get_enriched_financial_model() -> pd.DataFrame:
    model = FINANCIAL_STATEMENT_MODEL.copy()
    model['Path'] = model.index.map(get_measure_paths)
    return model


VALID_MEASURES: Set[str] = set(FINANCIAL_STATEMENT_MODEL.index.str.strip())
LINE_ITEMS: Set[str] = VALID_MEASURES - get_fin_statement_descendants_and_self('Ratios')
