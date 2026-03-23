import streamlit as st
from a_Config.global_constants import DERIVE_RATIOS, LINE_ITEMS
from a_Config.enumerations import ChangeType
from a_Config.fin_statement_model_utils import get_fin_statement_descendants
from c_Processing.c_main_data_pipeline import create_full_underived_df, to_dataset
from d_Transformations.aggregations import create_failed_dataset, calc_population_aggregates, calc_aggregates
from d_Transformations.derived_ratio_pipeline import run_derived_ratio_pipeline
from d_Transformations.change_pipeline import run_change_pipeline, calc_period_over_period_change
from e_Visualizations.failed_histogram import plot_failed_histogram
from e_Visualizations.mean_bar_charts import plot_mean_bar_chart
from e_Visualizations.leadup_to_failure import plot_leadup_to_failure, plot_cum_leadup_to_failure


#######################################################################################################
# User Inputs
#######################################################################################################

# st.sidebar.markdown("Analysis Parameters")

ratios_or_changes = st.sidebar.radio('Measure Source', ['Ratios', 'Income Statement (Changes)', 'Balance Sheet (Changes)'])
use_ratios = ratios_or_changes == 'Ratios'

derived_ratios = list(DERIVE_RATIOS['Measure'].unique())
income_statement_items = get_fin_statement_descendants('Total Surplus/Deficit')
balance_sheet_items = get_fin_statement_descendants('Total Unrestricted Assets') | get_fin_statement_descendants('Total Liabilities and Equity')
match ratios_or_changes: 
    case 'Ratios': 
        measure_options = derived_ratios 
    case 'Income Statement (Changes)': 
        measure_options = income_statement_items
    case 'Balance Sheet (Changes)': 
        measure_options = balance_sheet_items

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

num_years_ma = st.sidebar.number_input(
    'Lookback Years',
    1, 10, 5
)

#######################################################################################################
# Data
#######################################################################################################

underived_df = create_full_underived_df(selected_states)

if not use_full_window:
    year_index = underived_df.index.get_level_values('Year').astype(int)
    underived_df = underived_df[(year_index >= year_begin) & (year_index <= year_end)]

underived_ds = to_dataset(underived_df)

derived_ratio_ds = run_derived_ratio_pipeline(underived_ds, num_years_ma)
# failed_ratio_ds = create_failed_dataset(derived_ratio_ds, num_years_ma + 1)

change_ds = calc_period_over_period_change(underived_ds, 'value', num_years_ma)
# failed_change_ds = create_failed_dataset(change_ds, num_years_ma + 1)

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

st.set_page_config(
    page_title="Hospital Cross-Sectional Analysis",
    page_icon="🏥",
    layout="wide"
)

st.title("What are the financial characteristics of failed hospitals?")

#######################################################################################################
# Intro Charts
#######################################################################################################

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
