from email.policy import default
import streamlit as st
import xarray as xr
from a_Config.enumerations.change_or_level_enum import ChangeOrLevel
from a_Config.enumerations.interface_fields_enum import InterfaceFields
from a_Config.global_constants import DERIVE_RATIOS, LINE_ITEMS, ALL_RATIOS, SYSTEMS_TO_HOSPITALS_MAP
from a_Config.enumerations import *
from a_Config.fin_statement_model_utils import get_fin_statement_descendants
from e_Data_Pipelines.e_run_full_entity_pipeline import run_full_entity_pipeline
from f_Aggregations.aggregations import create_failed_dataset, calc_population_aggregates, calc_aggregates
from e_Data_Pipelines.c_change_pipeline import calc_pct_changes
from g_Visualizations.failed_histogram import plot_failed_histogram
from g_Visualizations.mean_bar_charts import plot_mean_bar_chart
from g_Visualizations.leadup_to_failure import plot_leadup_to_failure, plot_cum_leadup_to_failure
from g_Visualizations.measure_scatter import plot_measure_scatter
from g_Visualizations.r2_table import calc_r2_table
from g_Visualizations.measure_comparison_table import calc_measure_comparison_table
from g_Visualizations.hospitals_per_measure_table import hospitals_per_measure_table


st.set_page_config(
    page_title="Hospital Cross-Sectional Analysis",
    page_icon="🏥",
    layout="wide"
)

#######################################################################################################
# Cached pipeline helpers
#######################################################################################################

@st.cache_data
def _build_entity_datasets(states: tuple, num_years_ma: int, entities: frozenset, year_begin=None, year_end=None):
    return run_full_entity_pipeline(list(states), num_years_ma, entities=entities, year_start=year_begin, year_end=year_end)


@st.cache_data
def _cached_r2_table(states: tuple, num_years_ma: int, entities: frozenset, year_begin, year_end, x_measure: str, measures: tuple, x_change_or_level: ChangeOrLevel, y_change_or_level: ChangeOrLevel, y_lag: int):
    _, _, combined_ds = _build_entity_datasets(states, num_years_ma, entities, year_begin, year_end)
    return calc_r2_table(combined_ds, x_measure, list(measures), x_change_or_level, y_change_or_level, y_lag=y_lag)


#######################################################################################################
# User Inputs
#######################################################################################################

###### Measure Configs #######

measure_source = MeasureSource(
    st.sidebar.radio('Measure Source', [e.value for e in MeasureSource])
)

use_ratios = measure_source == MeasureSource.RATIOS

derived_ratios = list(DERIVE_RATIOS['Measure'].unique())
income_statement_items = list(get_fin_statement_descendants('Total Surplus/Deficit'))
balance_sheet_items = list(get_fin_statement_descendants('Total Unrestricted Assets') | get_fin_statement_descendants('Total Liabilities and Equity'))
match measure_source:
    case MeasureSource.RATIOS:
        measure_options = derived_ratios
    case MeasureSource.INCOME_STATEMENT:
        measure_options = income_statement_items
    case MeasureSource.BALANCE_SHEET:
        measure_options = balance_sheet_items
all_measure_options = derived_ratios + income_statement_items + balance_sheet_items

selected_measure = st.sidebar.selectbox('Measure', measure_options, 0)

change_or_level = ChangeOrLevel(
    st.sidebar.segmented_control('', options=[e.value for e in ChangeOrLevel], 
                                               default=ChangeOrLevel.LEVEL.value if use_ratios else ChangeOrLevel.CHANGE.value, label_visibility='collapsed')
)

###### Entity Configs #######

st.sidebar.markdown('---')

selected_states = st.sidebar.multiselect(
    'States', list(State), default=[State.ME], format_func=lambda s: s.value
)

hospitals_or_systems = st.sidebar.segmented_control('', options=['Hospitals', 'Systems'], default='Hospitals', label_visibility='collapsed')

available_systems = {
    f"{sys} ({state.value})": (sys, state)
    for sys, state in SYSTEMS_TO_HOSPITALS_MAP
    if state in selected_states
}
options = list(available_systems.keys())

selected_labels = st.sidebar.multiselect(
    'Systems Filter', options=options, default=options, key="systems_multiselect"
)
systems_to_include = {available_systems[label] for label in selected_labels}

if hospitals_or_systems == 'Hospitals':
    entities_to_include = {h for key in systems_to_include for h in SYSTEMS_TO_HOSPITALS_MAP[key]}
else:
    entities_to_include = {sys for sys, state in systems_to_include}

###### Analytical Configs #######

st.sidebar.markdown('---')

use_full_window = st.sidebar.checkbox('Use Full Window', value=True)

if not use_full_window:
    year_begin = st.sidebar.number_input('Begin Year', min_value=2000, max_value=2025, value=2000, step=1)
    year_end = st.sidebar.number_input('End Year', min_value=2000, max_value=2025, value=2025, step=1)
    if year_begin >= year_end:
        st.sidebar.error('Begin year must be before end year.')
        st.stop()
else:
    year_begin = None
    year_end = None

num_years_ma = st.sidebar.number_input(
    'Lookback Years',
    1, 10, 5
)

#######################################################################################################
# Data
#######################################################################################################

states_key = tuple(selected_states)
level_ds, change_ds, combined_ds = _build_entity_datasets(states_key, num_years_ma, frozenset(entities_to_include), year_begin, year_end)

is_use_levels = change_or_level == ChangeOrLevel.LEVEL
active_ds = level_ds if is_use_levels else change_ds
failed_ds = create_failed_dataset(active_ds, num_years_ma + 1)
last_col = InterfaceFields.ENDPOINT if is_use_levels else InterfaceFields.CHANGE
ma_col = InterfaceFields.MA if is_use_levels else InterfaceFields.MA_OF_CHANGE
change_type = ChangeType.ARITHMETIC if use_ratios else ChangeType.GEOMETRIC

aggregate_ds = calc_population_aggregates(active_ds, var=last_col, change_type=change_type)
ma_aggregate_ds = calc_population_aggregates(active_ds, var=ma_col, change_type=change_type)
failed_aggregate_ds = calc_aggregates(failed_ds, last_col, change_type, year_dim='relative_year')
failed_ma_aggregate_ds = calc_aggregates(failed_ds, ma_col, change_type, year_dim='relative_year')

#######################################################################################################
# Viz Helpers
#######################################################################################################

if is_use_levels:
    change_in_text = ""
elif use_ratios:
    change_in_text = "Change in "
else:
    change_in_text = "% Change in "

default_title = f'{change_in_text}{selected_measure}'

state_subtitle_str = ", ".join(state.value for state in selected_states)

subtitle_year_begin = year_begin or int(active_ds.year.values.min())
subtitle_year_end = year_end or int(active_ds.year.values.max())
default_subtitle = f'{state_subtitle_str}, {subtitle_year_begin}-{subtitle_year_end}'

#######################################################################################################
# App
#######################################################################################################

st.title("Understanding the financial characteristics of failed hospitals.")

#######################################################################################################
# Comparison of Measure vs Failed
#######################################################################################################

###### Histogram ######

margin = 0.3
_, col, side_col = st.columns([0.1, 1, margin])

with side_col:
    is_use_ma_for_hist = st.radio('', [e.value for e in MovingAvgOrEndpoint], label_visibility='collapsed') == MovingAvgOrEndpoint.MOVING_AVG.value

non_failed_mean = float(aggregate_ds[InterfaceFields.MEAN].sel(population='non_failed', measure=selected_measure, year='Total'))
non_failed_std_dev = float(aggregate_ds[InterfaceFields.STD].sel(population='non_failed', measure=selected_measure, year='Total'))

with col:
    lb, ub = (None, None) if use_ratios else (-1, 3)
    ma_title = f' ({num_years_ma}yma)' if is_use_ma_for_hist else ''
    st.plotly_chart(
        plot_failed_histogram(
            active_ds,
            failed_ds,
            selected_measure,
            var=(ma_col if is_use_ma_for_hist else last_col),
            ma_years=num_years_ma if is_use_ma_for_hist else None,
            clip_lower=lb, clip_upper=ub,
            title=f'Distribution of {default_title}{ma_title}',
            subtitle=default_subtitle
        ),
        use_container_width=True
    )

###### Bar Chart Before Failing ######

col1, _, col2 = st.columns([1, 0.2, 2])

with col1:
    failed_year_mean = float(failed_aggregate_ds[InterfaceFields.MEAN].sel(measure=selected_measure, relative_year=0))
    failed_year_std = float(failed_aggregate_ds[InterfaceFields.STD].sel(measure=selected_measure, relative_year=0))
    failed_ma_mean = float(failed_ma_aggregate_ds[InterfaceFields.MEAN].sel(measure=selected_measure, relative_year=-1))
    failed_ma_std = float(failed_ma_aggregate_ds[InterfaceFields.STD].sel(measure=selected_measure, relative_year=-1))
    st.plotly_chart(
        plot_mean_bar_chart(
            [
                (non_failed_mean, non_failed_std_dev),
                (failed_year_mean, failed_year_std),
                (failed_ma_mean, failed_ma_std),
            ],
            ['Operational', 'Failed Year', f'{num_years_ma}yma Before Failing'],
            title=f'Mean {default_title} +/- 1 Std. Dev.',
            subtitle=default_subtitle,
            measure=selected_measure,
        )
    )

###### Leadup to Failure Chart ######

with col2:
    if use_ratios:
        st.plotly_chart(
            plot_leadup_to_failure(
                failed_ds[last_col].sel(measure=selected_measure),
                non_failed_mean,
                non_failed_std_dev,
                yaxis_title=selected_measure,
                title=f'Lead Up to Failure vs Population: {default_title}',
                subtitle=default_subtitle,
                measure=selected_measure,
            )
        )
    else:
        st.plotly_chart(
            plot_cum_leadup_to_failure(
                failed_ds[InterfaceFields.CUM_CHANGE].sel(measure=selected_measure),
                non_failed_mean,
                non_failed_std_dev,
                yaxis_title=f'{selected_measure}\n(Cum. % Change)',
                title=f'Lead Up to Failure vs Population: {default_title}',
                subtitle=default_subtitle,
                measure=selected_measure,
            )
        )

###### Sorted Hospitals Per Measure ######

hospitals_per_measure_expander = st.expander(f'All {selected_measure} Values', expanded=False)

with hospitals_per_measure_expander:
    st.dataframe(hospitals_per_measure_table(active_ds, selected_measure, last_col, ma_col, num_years_ma))

###### All Measures Exploration ######

st.subheader("All Measures: Operational vs. Failed")
st.dataframe(calc_measure_comparison_table(aggregate_ds, ma_aggregate_ds, failed_aggregate_ds, failed_ma_aggregate_ds, measure_options))

#######################################################################################################
# Comparison to Other Measures
#######################################################################################################

st.header("Comparison vs Other Measures")

###### Scatter vs Other Measure ######

margin = 0.3
_, col, side_col = st.columns([margin, 1, margin])

with side_col:
    scatter_measure_x = st.selectbox('Scatter X-Axis Measure', all_measure_options, min(3, len(measure_options) - 1))
    endpoint_or_ma = MovingAvgOrEndpoint(
        st.radio('', [e.value for e in MovingAvgOrEndpoint], label_visibility='collapsed', key='for_scatter')
        )
    x_change_or_level = ChangeOrLevel(st.segmented_control('', options=[e.value for e in ChangeOrLevel], default=ChangeOrLevel.LEVEL.value if use_ratios else ChangeOrLevel.CHANGE.value, label_visibility='collapsed'))
    x_lag = st.number_input('Lag X-Axis Measure', min_value=-10, max_value=10, value=0, step=1, help='Positive values shift the X-axis measure forward in time, so X at year T is paired with Y at year T+lag.')

with col:
    scatter_da = combined_ds[InterfaceFields.ENDPOINT] if endpoint_or_ma == MovingAvgOrEndpoint.ENDPOINT else combined_ds[InterfaceFields.MA]
    st.plotly_chart(plot_measure_scatter(
        scatter_da.sel(measure=scatter_measure_x, change_or_level=x_change_or_level),
        scatter_da.sel(measure=selected_measure, change_or_level=change_or_level),
        combined_ds[InterfaceFields.YEAR_FAILED],
        x_lag=x_lag,
    ))

    def _styled(df):
        return (df.style
                .background_gradient(cmap='Blues', subset=['Last R²', 'MA R²'], vmin=0, vmax=1)
                .format({'Last R²': '{:.2f}', 'MA R²': '{:.2f}'}))

    with st.expander("R² vs Ratios", expanded=True):
        st.dataframe(_styled(_cached_r2_table(states_key, num_years_ma, frozenset(entities_to_include), year_begin, year_end, selected_measure, tuple(derived_ratios), change_or_level, x_change_or_level, x_lag)), hide_index=True, use_container_width=True)

    with st.expander("R² vs Change in Income Statement Items", expanded=False):
        st.dataframe(_styled(_cached_r2_table(states_key, num_years_ma, frozenset(entities_to_include), year_begin, year_end, selected_measure, tuple(income_statement_items), change_or_level, x_change_or_level, x_lag)), hide_index=True, use_container_width=True)

    with st.expander("R² vs Change in Balance Sheet Items", expanded=False):
        st.dataframe(_styled(_cached_r2_table(states_key, num_years_ma, frozenset(entities_to_include), year_begin, year_end, selected_measure, tuple(balance_sheet_items), change_or_level, x_change_or_level, x_lag)), hide_index=True, use_container_width=True)