# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Apps

```bash
# Individual hospital analysis
streamlit run src/main.py

# Cross-sectional analysis
streamlit run src/analysis_app.py
```

## Formatting
- Always strive to use idiomatic Python
- Prefer to use non-string types
- By and large, all files should contain a single function with the exception being small helper functions

No formal test suite or linter is configured.

## Architecture

The pipeline flows through alphabetically-ordered subdirectories in `src/`:

```
b_Ingest → c_Fin_Statement_Processing → d_Transformations → e_Data_Pipelines → f_Aggregations → g_Visualizations → Streamlit apps
```

**Data structure transition**: Raw ingestion produces a pandas DataFrame with a MultiIndex `(Organization, State, Measure, Year)` and columns `Value` / `Year Failed`. `c_Fin_Statement_Processing/e_main_data_pipeline.py` converts this to an **xarray Dataset** with dims `(organization, state, measure, year)`, one data variable `value`, and a `year_failed` coordinate. Downstream pipelines in `e_Data_Pipelines/` derive additional variables on top of this.

### Key layers

**`a_Config/`** — Configuration loaded once at startup
- `csv_configs/fin_statement_model.csv`: defines the financial statement measure hierarchy (parent/child relationships, negate flags)
- `csv_configs/derive_ratios.csv`: rules for computing derived ratios (numerator/denominator components, multipliers, optional flag)
- `csv_configs/external_mappings.csv`: maps state-reported measure names → standardized internal names
- `csv_configs/hospital_metadata.csv`: contains `Year Failed` per hospital — the core dependent variable; also `Healthcare System` membership
- `fin_statement_model_utils.py`: ancestor/descendant lookup functions; exposes `FINANCIAL_STATEMENT_MODEL`, `VALID_MEASURES`, `LINE_ITEMS`, `ALL_RATIOS`
- `global_constants.py`: loads all CSVs and exposes constants including `HOSPITAL_METADATA`, `SYSTEMS_TO_HOSPITALS_MAP`, `DERIVE_RATIOS`; also `get_measure_tickformat(measure)` → Plotly format string (`.1%` for Percent, `.1f` for Float, `$,.1f` for Millions)
- `enumerations/`: `ChangeType` (ARITHMETIC vs GEOMETRIC), `ChangeOrLevel` (LEVEL vs CHANGE), `InterfaceFields` (endpoint, ma, change, ma_of_change, cum_change, …), `State`, `Hospital`, `HealthSystem`, `Population`, `MeasureSource`

**`b_Ingest/`** — Parses raw data
- `a_ingest_me_financials.py`: parses Maine PDFs/CSVs; standardizes hospital and measure names
- `b_ingest_ma_financials.py`: reads MA CSVs; converts wide → long format; handles dollar-string parsing
- `z_get_financials_by_state.py`: routes ingestion by state via a dispatch dict — add new states here

**`c_Fin_Statement_Processing/`** — Cleaning and transformation to xarray
- `a_external_to_internal_mapping.py`: maps external measure names → standardized internal names via `external_mappings.csv`
- `b_calculate_children_sums.py` / `c_add_imputed_sum_of_children_rows.py`: computes parent line items as sums of children per the hierarchy; only inserts a computed parent if **all** expected children are present
- `d_impute_systems_from_hospitals.py`: aggregates hospital-level rows into health-system-level rows
- `e_main_data_pipeline.py`: orchestrates ingest → map → sum-of-children → system imputation → xarray conversion; `load_pre_transformed_dataset()` is the public entry point (cached with `@st.cache_data`)
- `h_calculate_residuals.py`: balance sheet residuals (sum-of-children minus parent, surfacing accounting discrepancies)

**`d_Transformations/`** — Derived calculations on xarray
- `a_take_moving_average.py`: rolling window MA over the year dimension
- `b_derived_ratios.py`: computes ratio measures from line-item DataArrays (num/denom from `derive_ratios.csv`)
- `c_normalize_measures.py`: normalizes measures
- `d_calc_pct_changes.py` / `e_calc_arith_changes.py`: period-over-period % change and arithmetic change

**`e_Data_Pipelines/`** — Orchestrates transformations into unified xarray outputs
- `a_dollar_level_pipeline.py`: MA of raw dollar line items → `value` + `ma`
- `b_run_level_pipeline.py`: `run_level_pipeline(ds, ma_years)` → Dataset with `InterfaceFields.ENDPOINT` and `InterfaceFields.MA` for all measures (line items + derived ratios). Ratio order matters: derive ratios from endpoint values first, then derive MA ratios from MA values (so MA(num)/MA(denom), not MA(ratio))
- `c_change_pipeline.py`: `run_change_pipeline(level_ds, ma_years)` → Dataset with `change`, `ma_of_change`, `cum_change`
- `d_run_combined_pipeline.py`: `run_combined_pipeline(level_ds, change_ds)` → Dataset with a `change_or_level` dimension (ChangeOrLevel.LEVEL / ChangeOrLevel.CHANGE), normalized to `endpoint` + `ma` variables
- `e_run_full_entity_pipeline.py`: top-level entry — calls ingest + all pipelines, returns `(level_ds, change_ds, combined_ds)`

**`f_Aggregations/`**
- `aggregations.py`: `calc_aggregates()` (mean/std per year + Total, supports GEOMETRIC mode via log1p), `calc_population_aggregates()` (splits into total/failed/non_failed populations), `create_failed_dataset()` (reindexes failed hospitals by `relative_year` where 0 = failure year), `filter_to_non_failed()`

**`g_Visualizations/`** — Chart builders called from the Streamlit apps. Use `get_measure_tickformat()` for axis formatting — never hardcode percentage vs. float format.

### Streamlit apps

- **`analysis_app.py`**: cross-sectional view — compares distributions of failed vs. operational hospitals; controls for analysis period, years-before-failing window, states, measure type
- **`main.py`** / **`individual_hospital_app.py`**: individual hospital deep-dive — hierarchical tables for ratios, income statement, balance sheet, plus balance sheet residuals

## Data

- Raw PDFs and CSVs: `src/z_Data/Raw_Data/`
- Preprocessed outputs: `src/z_Data/Preprocessed_Data/`
