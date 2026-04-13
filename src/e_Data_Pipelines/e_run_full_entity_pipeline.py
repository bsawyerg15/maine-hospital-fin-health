"""
Runs the full analysis pipeline (ingest → level → change → combined) for a
filtered set of entities. Caching is left to the calling app.
"""
import xarray as xr
from a_Config.enumerations.state_enum import State
from c_Fin_Statement_Processing.e_main_data_pipeline import load_pre_transformed_dataset
from e_Data_Pipelines.b_run_level_pipeline import run_level_pipeline
from e_Data_Pipelines.c_change_pipeline import run_change_pipeline
from e_Data_Pipelines.d_run_combined_pipeline import run_combined_pipeline


def run_full_entity_pipeline(
    states: list[State],
    num_years_ma: int,
    entities=None,
    year_start=None,
    year_end=None,
) -> tuple[xr.Dataset, xr.Dataset, xr.Dataset]:
    underived_ds = load_pre_transformed_dataset(states, entities=entities, year_start=year_start, year_end=year_end)
    level_ds = run_level_pipeline(underived_ds, num_years_ma)
    change_ds = run_change_pipeline(level_ds, num_years_ma)
    combined_ds = run_combined_pipeline(level_ds, change_ds)
    return level_ds, change_ds, combined_ds
