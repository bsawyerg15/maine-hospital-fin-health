import streamlit as st
import pandas as pd
import os
from b_Ingest.ingest_me_financials import create_combined_me_financial_df
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode, GridUpdateMode
from a_Config.global_constants import FINANCIAL_STATEMENT_MODEL
from c_Processing.b_sum_of_children import calculate_residuals
from c_Processing.c_main_data_pipeline import process_financial_df
from d_Transformations.aggregations import create_mean_df, create_failed_hospital_df, filter_to_non_failed_hospitals
from d_Transformations.moving_average import take_moving_average
from d_Transformations.derived_ratios import derive_ratios
from e_Visualizations.aggrid_utils import create_hierarchical_aggrid
from e_Visualizations.failed_histogram import plot_failed_histogram
from e_Visualizations.mean_bar_charts import plot_mean_bar_chart
from e_Visualizations.leadup_to_failure import plot_leadup_to_failure

#######################################################################################################
# User Inputs
#######################################################################################################

selected_date = st.sidebar.selectbox(
    'Analysis Period End',
    options=['Total'] + sorted([str(i) for i in range(2000, 2025)], reverse=True),
    index=0
)

num_years_ma = st.sidebar.number_input(
    'Number of Years Before Failing',
    1, 10, 5
)

selected_states = st.sidebar.multiselect(
    'States', ['ME', 'MA'], default=['ME']
)

# is_restrict_failed = st.sidebar.checkbox(
#     'Restrict Failed to Analysis Period',
#     help='Checking this will only include hospitals that failed within analysis period in the top charts.'
# )

#######################################################################################################
# Data Inputs
#######################################################################################################

dfs = []
for state in selected_states:
    df = process_financial_df(state)
    dfs.append(df)
hospital_df = pd.concat(dfs)

mean_df = create_mean_df(hospital_df)

failed_hospital_df = create_failed_hospital_df(hospital_df, num_years_ma + 1)

all_ratios_comparison_df = filter_to_non_failed_hospitals(hospital_df)

mean_failed_df = failed_hospital_df.groupby(level='Measure').mean()

non_failed_mean_df = create_mean_df(all_ratios_comparison_df)

ma_failed_df = take_moving_average(mean_failed_df, num_years_ma)

derived_ratios_df = derive_ratios(hospital_df)

derived_ma_ratios_df = derive_ratios(take_moving_average(hospital_df, num_years_ma))

failed_derived_ratios_df = create_failed_hospital_df(derived_ratios_df, num_years_ma + 1)

failed_derived_ma_ratios_df = create_failed_hospital_df(derived_ma_ratios_df, num_years_ma + 1)

non_failed_derived_ratios_df = filter_to_non_failed_hospitals(derived_ratios_df)

non_failed_derived_ma_ratios_df = take_moving_average(non_failed_derived_ratios_df, num_years_ma)

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
    selected_measure = st.selectbox('Measure', derived_ratios_df.index.get_level_values(1).unique(), 2)
    is_use_ma_for_hist = st.radio('', ['Endpoint', 'Moving Avg']) == 'Moving Avg'

non_failed_df = non_failed_derived_ratios_df.xs(selected_measure, level='Measure')

all_non_failed_values = non_failed_df.stack()
non_failed_mean = all_non_failed_values.mean()
non_failed_std_dev = all_non_failed_values.std()

histogram_non_failed_vals = non_failed_derived_ma_ratios_df.xs(selected_measure, level='Measure').stack() if is_use_ma_for_hist else all_non_failed_values
histogram_failed_df = failed_derived_ratios_df if not is_use_ma_for_hist else failed_derived_ma_ratios_df

with col:
    st.plotly_chart(
        plot_failed_histogram(
            histogram_non_failed_vals,
            histogram_failed_df.xs(selected_measure, level='Measure')['T - 1'],
            selected_measure,
            ma_years = num_years_ma if is_use_ma_for_hist else None,
            ),
            use_container_width=True
    )

col1, _, col2 = st.columns([1, 0.2, 2])

with col1:
    st.plotly_chart(
        plot_mean_bar_chart([derived_ratios_df.xs(selected_measure, level='Measure').stack(), 
                             failed_derived_ratios_df.xs(selected_measure, level='Measure')['T'],
                             failed_derived_ma_ratios_df.xs(selected_measure, level='Measure')['T - 1']
                             ], ['Operational', 'Failed Year', f'{num_years_ma}yma Before Failing'],
                             title=f'Mean {selected_measure} +/- 1 Std. Dev.'
                             )
        )
    
with col2:
    st.plotly_chart(
        plot_leadup_to_failure(failed_derived_ratios_df.xs(selected_measure, level='Measure'),
                               non_failed_mean,
                               non_failed_std_dev,
                               yaxis_title=selected_measure, title=f'Lead Up to Failure vs Population: {selected_measure}')
    )

#######################################################################################################
# Tables
#######################################################################################################

all_ratios_comparison_df = non_failed_mean_df[[selected_date]].join(ma_failed_df[['T - 1']])
all_ratios_comparison_df.columns = ['Operating', '3yma Before Failing']
all_ratios_comparison_df['Diff'] = all_ratios_comparison_df['3yma Before Failing'] - all_ratios_comparison_df['Operating']
all_ratios_comparison_df = all_ratios_comparison_df.round(1)

create_hierarchical_aggrid(all_ratios_comparison_df, ['Ratios'])

st.dataframe(derived_ratios_df)

st.dataframe(derived_ma_ratios_df)