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
b_Ingest → c_Processing → d_Transformations → e_Visualizations → Streamlit apps
```

**Data structure transition**: Raw ingestion produces a pandas DataFrame with a MultiIndex `(Organization, State, Measure, Year)` where `Organization` can be a hospital or health system and columns `Value` / `Year Failed`. This is converted to an **xarray Dataset** at the end of `c_Processing/c_main_data_pipeline.py`, with dimensions `(organization, state, measure, year)` and data variables `value`, `endpoint`, `ma`, `pct_change_*`, `ln_change_*`. All `d_Transformations/` modules operate on xarray.

### Key layers

**`a_Config/`** — Configuration loaded once at startup
- `fin_statement_model.csv`: defines the financial statement measure hierarchy (parent/child relationships, negate flags)
- `derive_ratios.csv`: rules for computing derived ratios (numerator/denominator components, multipliers)
- `external_mappings.csv`: maps state-reported measure names → standardized internal names
- `hospital_metadata.csv`: contains `year_failed` per hospital — the core dependent variable
- `fin_statement_model_utils.py`: ancestor/descendant lookup functions for the measure hierarchy
- `global_constants.py`: loads all CSVs and exposes `FINANCIAL_STATEMENT_MODEL`, `VALID_MEASURES`, `LINE_ITEMS`, `DERIVE_RATIOS`, `ALL_RATIOS`; also `get_measure_tickformat(measure)` → Plotly format string (`.1%` for Percent, `.1f` for Float)
- `enumerations/change_type.py`: `ChangeType.ARITHMETIC` (direct mean/std, used for ratios) vs `ChangeType.GEOMETRIC` (log-transform → mean/std → expm1, used for percent changes)

**`b_Ingest/`** — Parses raw data
- `ingest_me_financials.py`: parses Maine PDFs/CSVs; standardizes hospital and measure names
- `ingest_ma_financials.py`: reads MA CSVs; converts wide → long format; handles dollar-string parsing
- `ingest_union.py`: routes ingestion by state via `_STATE_DISPATCH` dict — add new states here by extending the dict and implementing a corresponding ingest function

**`c_Processing/`** — Cleaning and transformation
- `a_external_to_internal_mapping.py`: aggregates external measures into standardized internal measures
- `b_sum_of_children.py`: computes parent line items as sums of children per the hierarchy; only inserts a computed parent if **all** expected children are present
- `c_main_data_pipeline.py`: orchestrates ingest → map → filter → sum-of-children → xarray conversion

**`d_Transformations/`** — Derived calculations on xarray
- `derived_ratio_pipeline.py`: the correct order matters — (1) MA of raw measures, (2) endpoint ratios from raw, (3) MA ratios from MA of raw (so MA(num)/MA(denom), not MA(ratio))
- `aggregations.py`: `create_failed_dataset()` filters to failed hospitals and reindexes by `relative_year` (0 = failure year, -1 = one year prior, etc.)
- `calc_changes.py`: period-over-period % change and log change (used for Line Items analysis)

**`e_Visualizations/`** — Altair/Plotly chart builders called from the Streamlit apps. Use `get_measure_tickformat()` for axis formatting — never hardcode percentage vs. float format.

### Two Streamlit apps

- **`analysis_app.py`**: cross-sectional view — compares distributions of failed vs. operational hospitals; controls for analysis period, years-before-failing window, states, measure type (Ratios vs. Line Items)
- **`main.py`**: individual hospital deep-dive — hierarchical tables for ratios, income statement, balance sheet, plus balance sheet residuals (sum-of-children minus parent, surfacing accounting discrepancies)

## Data

- Raw PDFs and CSVs: `src/z_Data/Raw_Data/`
- Preprocessed outputs: `src/z_Data/Preprocessed_Data/`
