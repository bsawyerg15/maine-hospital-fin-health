import streamlit as st
import xarray as xr
from a_Config.global_constants import DERIVE_RATIOS, LINE_ITEMS, ALL_RATIOS
from a_Config.enumerations import ChangeType
from a_Config.fin_statement_model_utils import get_fin_statement_descendants
from c_Processing.c_main_data_pipeline import create_full_underived_df, to_dataset
from d_Transformations.aggregations import create_failed_dataset, calc_population_aggregates, calc_aggregates
from d_Transformations.derived_ratio_pipeline import run_derived_ratio_pipeline
from d_Transformations.change_pipeline import run_change_pipeline, calc_period_over_period_change
from e_Visualizations.failed_histogram import plot_failed_histogram
from e_Visualizations.mean_bar_charts import plot_mean_bar_chart
from e_Visualizations.leadup_to_failure import plot_leadup_to_failure, plot_cum_leadup_to_failure
from e_Visualizations.measure_scatter import plot_measure_scatter
from e_Visualizations.r2_table import calc_r2_table
from e_Visualizations.measure_comparison_table import calc_measure_comparison_table


st.set_page_config(
    page_title="Hospital Cross-Sectional Analysis",
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
def _build_datasets(states: tuple, num_years_ma: int, year_begin=None, year_end=None):
    df = _load_underived(states)
    if year_begin is not None and year_end is not None:
        year_index = df.index.get_level_values('Year').astype(int)
        df = df[(year_index >= year_begin) & (year_index <= year_end)]
    underived_ds = to_dataset(df)
    derived_ratio_ds = run_derived_ratio_pipeline(underived_ds, num_years_ma)
    dollar_level_ds = underived_ds.sel(measure=[m for m in underived_ds.coords['measure'].values if m not in ALL_RATIOS])
    change_ds = calc_period_over_period_change(dollar_level_ds, 'value', num_years_ma)
    interface_ds = xr.Dataset({
        'last':        xr.concat([derived_ratio_ds['endpoint'], change_ds['pct_change']], dim='measure'),
        'ma':          xr.concat([derived_ratio_ds['ma'], change_ds['ma_pct_change']], dim='measure'),
        'year_failed': derived_ratio_ds['year_failed'],
    })
    return derived_ratio_ds, change_ds, interface_ds


@st.cache_data
def _cached_r2_table(states: tuple, num_years_ma: int, year_begin, year_end, x_measure: str, measures: tuple, y_lag: int):
    _, _, interface_ds = _build_datasets(states, num_years_ma, year_begin, year_end)
    return calc_r2_table(interface_ds, x_measure, list(measures), y_lag=y_lag)


#######################################################################################################
# User Inputs
#######################################################################################################

ratios_or_changes = st.sidebar.radio('Measure Source', ['Ratios', 'Income Statement (Changes)', 'Balance Sheet (Changes)'])
use_ratios = ratios_or_changes == 'Ratios'

derived_ratios = list(DERIVE_RATIOS['Measure'].unique())
income_statement_items = list(get_fin_statement_descendants('Total Surplus/Deficit'))
balance_sheet_items = list(get_fin_statement_descendants('Total Unrestricted Assets') | get_fin_statement_descendants('Total Liabilities and Equity'))
match ratios_or_changes:
    case 'Ratios':
        measure_options = derived_ratios
    case 'Income Statement (Changes)':
        measure_options = income_statement_items
    case 'Balance Sheet (Changes)':
        measure_options = balance_sheet_items
all_measure_options = derived_ratios + income_statement_items + balance_sheet_items

selected_measure = st.sidebar.selectbox('Measure', measure_options, 2)

selected_states = st.sidebar.multiselect(
    'States', ['ME', 'MA'],
    default=['ME']
)

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
derived_ratio_ds, change_ds, interface_ds = _build_datasets(states_key, num_years_ma, year_begin, year_end)

active_ds = derived_ratio_ds if use_ratios else change_ds
failed_ds = create_failed_dataset(active_ds, num_years_ma + 1)
last_col = 'endpoint' if use_ratios else 'pct_change'
ma_col = 'ma' if use_ratios else 'ma_pct_change'
change_type = ChangeType.ARITHMETIC if use_ratios else ChangeType.GEOMETRIC

aggregate_ds = calc_population_aggregates(active_ds, var=last_col, change_type=change_type)
ma_aggregate_ds = calc_population_aggregates(active_ds, var=ma_col, change_type=change_type)
failed_aggregate_ds = calc_aggregates(failed_ds, last_col, change_type, year_dim='relative_year')
failed_ma_aggregate_ds = calc_aggregates(failed_ds, ma_col, change_type, year_dim='relative_year')

#######################################################################################################
# Viz
#######################################################################################################

st.title("What are the financial characteristics of failed hospitals?")

#######################################################################################################
# Comparison of Measure vs Failed
#######################################################################################################

###### Histogram ######

margin = 0.3
_, col, side_col = st.columns([0.1, 1, margin])

with side_col:
    is_use_ma_for_hist = st.radio('', ['Endpoint', 'Moving Avg']) == 'Moving Avg'

non_failed_mean = float(aggregate_ds['mean'].sel(population='non_failed', measure=selected_measure, year='Total'))
non_failed_std_dev = float(aggregate_ds['std'].sel(population='non_failed', measure=selected_measure, year='Total'))

with col:
    lb, ub = (None, None) if use_ratios else (-1, 3)
    st.plotly_chart(
        plot_failed_histogram(
            active_ds,
            failed_ds,
            selected_measure,
            var=(ma_col if is_use_ma_for_hist else last_col),
            ma_years=num_years_ma if is_use_ma_for_hist else None,
            clip_lower=lb, clip_upper=ub
        ),
        use_container_width=True
    )

###### Bar Chart Before Failing ######

col1, _, col2 = st.columns([1, 0.2, 2])

with col1:
    failed_year_mean = float(failed_aggregate_ds['mean'].sel(measure=selected_measure, relative_year=0))
    failed_year_std = float(failed_aggregate_ds['std'].sel(measure=selected_measure, relative_year=0))
    failed_ma_mean = float(failed_ma_aggregate_ds['mean'].sel(measure=selected_measure, relative_year=-1))
    failed_ma_std = float(failed_ma_aggregate_ds['std'].sel(measure=selected_measure, relative_year=-1))
    st.plotly_chart(
        plot_mean_bar_chart(
            [
                (non_failed_mean, non_failed_std_dev),
                (failed_year_mean, failed_year_std),
                (failed_ma_mean, failed_ma_std),
            ],
            ['Operational', 'Failed Year', f'{num_years_ma}yma Before Failing'],
            title=f'Mean {selected_measure} +/- 1 Std. Dev.',
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
                title=f'Lead Up to Failure vs Population: {selected_measure}',
                measure=selected_measure,
            )
        )
    else:
        st.plotly_chart(
            plot_cum_leadup_to_failure(
                failed_ds['cum_pct_change'].sel(measure=selected_measure),
                non_failed_mean,
                non_failed_std_dev,
                yaxis_title=f'{selected_measure}\n(Cum. % Change)',
                title=f'Lead Up to Failure vs Population: {selected_measure}',
                measure=selected_measure,
            )
        )

###### Sorted Hospitals Per Measure ######

hospitals_per_measure_expander = st.expander(f'All {selected_measure} Values', expanded=False)

with hospitals_per_measure_expander:
    available_years = sorted(int(y) for y in active_ds.coords['year'].values)
    selected_table_year = st.select_slider('Year', options=available_years, value=available_years[-1])

    table_df = active_ds.sel(measure=selected_measure, year=selected_table_year).to_dataframe()[[last_col, ma_col]].dropna().sort_values(last_col, ascending=False)
    st.dataframe(table_df)

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
    scatter_measure_y = st.selectbox('Scatter Y-Axis Measure', all_measure_options, min(3, len(measure_options) - 1))
    endpoint_or_ma = st.radio('', ['Endpoint', 'MA'])
    y_lag = st.number_input('Lag Y-Axis Measure', min_value=-10, max_value=10, value=0, step=1, help='Positive values shift the X-axis measure forward in time, so X at year T is paired with Y at year T+lag.')
with col:
    scatter_da = interface_ds['last'] if endpoint_or_ma == 'Endpoint' else interface_ds['ma']
    y_da = scatter_da.sel(measure=scatter_measure_y)
    if y_lag != 0:
        y_da = y_da.shift(year=y_lag)
    st.plotly_chart(plot_measure_scatter(
        scatter_da.sel(measure=selected_measure),
        y_da,
        interface_ds['year_failed'],
        y_lag=y_lag,
    ))

    def _styled(df):
        return (df.style
                .background_gradient(cmap='Blues', subset=['Last R²', 'MA R²'], vmin=0, vmax=1)
                .format({'Last R²': '{:.2f}', 'MA R²': '{:.2f}'}))

    with st.expander("R² vs Ratios", expanded=True):
        st.dataframe(_styled(_cached_r2_table(states_key, num_years_ma, year_begin, year_end, selected_measure, tuple(derived_ratios), y_lag)), hide_index=True, use_container_width=True)

    with st.expander("R² vs Change in Income Statement Items", expanded=False):
        st.dataframe(_styled(_cached_r2_table(states_key, num_years_ma, year_begin, year_end, selected_measure, tuple(income_statement_items), y_lag)), hide_index=True, use_container_width=True)

    with st.expander("R² vs Change in Balance Sheet Items", expanded=False):
        st.dataframe(_styled(_cached_r2_table(states_key, num_years_ma, year_begin, year_end, selected_measure, tuple(balance_sheet_items), y_lag)), hide_index=True, use_container_width=True)
