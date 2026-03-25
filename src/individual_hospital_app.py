import streamlit as st
from a_Config.global_constants import DERIVE_RATIOS, HOSPITAL_METADATA, ALL_RATIOS
from a_Config.fin_statement_model_utils import get_fin_statement_descendants
from c_Processing.c_main_data_pipeline import create_full_underived_df, to_dataset
from d_Transformations.derived_ratio_pipeline import run_derived_ratio_pipeline
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
    dollar_level_ds = underived_ds.sel(measure=[m for m in underived_ds.coords['measure'].values if m not in ALL_RATIOS])
    return dollar_level_ds, derived_ratio_ds


#######################################################################################################
# User Inputs
#######################################################################################################

derived_ratios = list(DERIVE_RATIOS['Measure'].unique())
income_statement_items = list(get_fin_statement_descendants('Total Surplus/Deficit'))
balance_sheet_items = list(get_fin_statement_descendants('Total Unrestricted Assets') | get_fin_statement_descendants('Total Liabilities and Equity'))

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
    active_var = 'value'
    # TODO: I should be able to select moving average for the levels. If not, I need to add this to the pipeline for non-ratio values

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

# TODO: Create a table of all the measures. For a given year, have columns:
# - Measure (index)
# - Hospital's value
# - Population value / Total Assets
# - Failed value / Total Assets
