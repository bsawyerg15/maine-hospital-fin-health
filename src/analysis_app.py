import streamlit as st
import pandas as pd
import os
from b_Ingest.ingest_me_financials import create_combined_me_financial_df
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode, GridUpdateMode
from a_Config.global_constants import FINANCIAL_STATEMENT_MODEL
from e_Visualizations.aggrid_utils import create_hierarchical_aggrid
from c_Processing.b_sum_of_children import calculate_residuals
from c_Processing.c_main_data_pipeline import process_financial_df
from d_Aggregations.aggregations import create_mean_df


#######################################################################################################
# Data Inputs
#######################################################################################################

hospital_df = process_financial_df('ME')

mean_df = create_mean_df(hospital_df)

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

create_hierarchical_aggrid(mean_df[[selected_date]].round(1), ['Ratios'])