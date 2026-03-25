import pandas as pd
import streamlit as st
from a_Config.global_constants import DERIVE_RATIOS, HOSPITAL_METADATA
from a_Config.fin_statement_model_utils import get_fin_statement_descendants_and_self
from c_Processing.c_main_data_pipeline import create_full_underived_df, to_dataset
from d_Transformations.derived_ratio_pipeline import run_derived_ratio_pipeline
from d_Transformations.dollar_level_pipeline import run_dollar_level_pipeline
from d_Transformations.normalize_measures import normalize_measures
from d_Transformations.aggregations import calc_population_aggregates
from e_Visualizations.hospital_time_series import plot_hospital_time_series

st.set_page_config(
    page_title="Individual Hospital Analysis",
    page_icon="🏥",
    layout="wide"
)


#######################################################################################################
# Cached pipeline helpers
#######################################################################################################

@st.cache_data
def _load_underived(states: tuple):
    return create_full_underived_df(list(states))


@st.cache_data
def _build_datasets(states: tuple, num_years_ma: int):
    df = _load_underived(states)
    underived_ds = to_dataset(df)
    derived_ratio_ds = run_derived_ratio_pipeline(underived_ds, num_years_ma)
    dollar_level_ds = run_dollar_level_pipeline(underived_ds, num_years_ma)
    return dollar_level_ds, derived_ratio_ds


@st.cache_data
def _normalize_dollar_ds(_dollar_level_ds, normalization_measure: str):
    return normalize_measures(_dollar_level_ds, normalization_measure, vars=['value', 'ma'])


#######################################################################################################
# User Inputs
#######################################################################################################

derived_ratios = list(DERIVE_RATIOS['Measure'].unique())
income_statement_items = list(get_fin_statement_descendants_and_self('Total Surplus/Deficit'))
balance_sheet_items = list(get_fin_statement_descendants_and_self('Total Unrestricted Assets') | get_fin_statement_descendants_and_self('Total Liabilities and Equity'))

selected_state = st.sidebar.selectbox('State', ['ME', 'MA'])

hospitals_in_state = sorted(
    org for org, state in HOSPITAL_METADATA.index if state == selected_state
)
selected_hospital = st.sidebar.selectbox('Hospital', hospitals_in_state)

measure_source = st.sidebar.radio(
    'Measure Source',
    ['Ratios', 'Income Statement (Changes)', 'Balance Sheet (Changes)']
)

match measure_source:
    case 'Ratios':
        measure_options = derived_ratios
    case 'Income Statement (Changes)':
        measure_options = income_statement_items
    case 'Balance Sheet (Changes)':
        measure_options = balance_sheet_items

selected_measure = st.sidebar.selectbox('Measure', measure_options)

NORMALIZATION_OPTIONS = ['Total Unrestricted Assets', 'Total Revenue', 'Total Operating Revenue']

if measure_source != 'Ratios':
    normalization = st.sidebar.selectbox('Normalization', NORMALIZATION_OPTIONS)
else:
    normalization = None

endpoint_or_ma = st.sidebar.radio('Value Type', ['Endpoint', 'Moving Avg'])

if endpoint_or_ma == 'Moving Avg':
    num_years_ma = st.sidebar.number_input('Lookback Years', 1, 10, 5)
else:
    num_years_ma = 5


#######################################################################################################
# Data
#######################################################################################################

dollar_level_ds, derived_ratio_ds = _build_datasets((selected_state,), num_years_ma)

if measure_source == 'Ratios':
    active_ds = derived_ratio_ds
    active_var = 'ma' if endpoint_or_ma == 'Moving Avg' else 'endpoint'
else:
    active_ds = dollar_level_ds
    active_var = 'ma' if endpoint_or_ma == 'Moving Avg' else 'value'

normalized_ds = _normalize_dollar_ds(dollar_level_ds, normalization)
aggregate_ds = calc_population_aggregates(active_ds, var=active_var)

#######################################################################################################
# Visualizations
#######################################################################################################

st.title(selected_hospital)

###### Line Chart ######

show_population = measure_source == 'Ratios'

hospital_da = active_ds[active_var].sel(organization=selected_hospital, state=selected_state, measure=selected_measure)
pop_mean_da = aggregate_ds['mean'].sel(population='total', measure=selected_measure)
pop_std_da = aggregate_ds['std'].sel(population='total', measure=selected_measure)

st.plotly_chart(
    plot_hospital_time_series(
        hospital_da,
        pop_mean_da=pop_mean_da if show_population else None,
        pop_std_da=pop_std_da if show_population else None,
        hospital_name=selected_hospital,
        measure=selected_measure,
        title=selected_measure,
    ),
    use_container_width=True,
)

###### Measure Table ######

available_years = sorted(int(y) for y in active_ds.coords['year'].values)
selected_year = st.selectbox('Year', available_years, index=len(available_years) - 1)

ds_measures = set(active_ds.coords['measure'].values)
table_measures = [m for m in measure_options if m in ds_measures]

hospital_vals = (
    active_ds[active_var]
    .sel(organization=selected_hospital, state=selected_state, measure=table_measures, year=selected_year)
    .to_series()
    .rename('Value')
    .round(2)
)

# TODO: add columns:
# - Population value / Total Assets
# - Failed value / Total Assets

st.dataframe(hospital_vals.to_frame(), use_container_width=True)


