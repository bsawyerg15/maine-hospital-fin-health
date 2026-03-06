import streamlit as st
import pandas as pd
import os
from b_Ingest.ingest_me_financials import create_combined_me_financial_df
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode, GridUpdateMode
from a_Config.global_constants import FINANCIAL_STATEMENT_MODEL
from c_Processing.b_sum_of_children import calculate_residuals
from c_Processing.c_main_data_pipeline import process_financial_df
from d_Transformations.aggregations import create_mean_df, create_failed_hospital_df
from d_Transformations.moving_average import take_moving_average
from d_Transformations.derived_ratios import derive_ratios
from e_Visualizations.aggrid_utils import create_hierarchical_aggrid
from e_Visualizations.failed_histogram import plot_failed_histogram
from e_Visualizations.mean_bar_charts import plot_mean_bar_chart
from e_Visualizations.leadup_to_failure import plot_leadup_to_failure


#######################################################################################################
# Data Inputs
#######################################################################################################

hospital_df = process_financial_df('ME')

mean_df = create_mean_df(hospital_df)

failed_hospital_df = create_failed_hospital_df(hospital_df)

mean_failed_df = failed_hospital_df.groupby(level='Measure').mean()

ma_failed_df = take_moving_average(mean_failed_df, 3)

derived_ratios_df = derive_ratios(hospital_df)

derived_ma_ratios_df = derive_ratios(take_moving_average(hospital_df, 3))

failed_derived_ratios_df = create_failed_hospital_df(derived_ratios_df)

failed_derived_ma_ratios_df = create_failed_hospital_df(derived_ma_ratios_df)

#######################################################################################################
# User Inputs
#######################################################################################################

selected_date = st.sidebar.selectbox(
    'Select Analysis Period',
    options=sorted(mean_df.columns, reverse=True),
    index=0
)

#######################################################################################################
# Viz
#######################################################################################################

st.set_page_config(
    page_title="Hospital Cross-Sectional Analysis",
    page_icon="🏥",
    layout="wide"
)

st.title("Cross Sectional Analysis")

margin = 0.3
_, col, side_col = st.columns([0.1, 1, margin])

with side_col:
    selected_measure = st.selectbox('Measure', derived_ratios_df.index.get_level_values(1).unique())

with col:
    st.plotly_chart(
        plot_failed_histogram(derived_ratios_df.xs(selected_measure, level='Measure'), 
                        failed_derived_ratios_df.xs(selected_measure, level='Measure'),
                        pop_column='2024', failed_column='T - 1'),
                        use_container_width=True
    )

    st.plotly_chart(
        plot_mean_bar_chart([derived_ratios_df.xs(selected_measure, level='Measure').stack(), 
                             failed_derived_ratios_df.xs(selected_measure, level='Measure')['T'],
                             failed_derived_ma_ratios_df.xs(selected_measure, level='Measure')['T - 1']
                             ], ['Population', 'Failed Year', '3yma Before Failing'])
        )
    
    st.plotly_chart(
        plot_leadup_to_failure(failed_derived_ratios_df.xs(selected_measure, level='Measure'),
                               mean=0.1, std=0.05)
    )

create_hierarchical_aggrid(mean_df[[selected_date]].join(ma_failed_df[['T - 1']]).round(1), ['Ratios'])

st.dataframe(derived_ratios_df)

st.dataframe(derived_ma_ratios_df)