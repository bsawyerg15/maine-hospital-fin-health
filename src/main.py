import streamlit as st
import pandas as pd
import os
from b_Ingest.ingest_me_financials import create_combined_me_financial_df
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode, GridUpdateMode
from a_Config.global_constants import FINANCIAL_STATEMENT_MODEL
from e_Visualizations.aggrid_utils import create_hierarchical_aggrid
from c_Processing.b_sum_of_children import calculate_residuals
from c_Processing.c_main_data_pipeline import process_financial_df
from d_Transformations.derived_ratios import derive_ratios


#######################################################################################################
# Data Inputs
#######################################################################################################

dollar_df = process_financial_df('MA')

residual_df = calculate_residuals(dollar_df)

derived_ratios_df = derive_ratios(dollar_df)

#######################################################################################################
# User Inputs
#######################################################################################################

st.sidebar.header("Navigation")
selected_organization = st.sidebar.selectbox(
    'Select Organization',
    options=sorted(dollar_df.index.get_level_values('Organization').unique().tolist()),
    index=0
)

#######################################################################################################
# Calcs
#######################################################################################################

hospital_df = dollar_df.xs(selected_organization, level='Organization')

hospital_derived_ratios_df = derived_ratios_df.xs(selected_organization, level='Organization')

hospital_residual_df = residual_df.xs(selected_organization, level='Organization')

#######################################################################################################
# Viz
#######################################################################################################

# Page configuration
st.set_page_config(
    page_title="Hospital Financial Profile",
    page_icon="🏥",
    layout="wide"
)

# Title
st.title(f"{selected_organization} Financial Profile")

st.subheader("Ratios")
create_hierarchical_aggrid(hospital_df, ['Ratios'])

st.subheader("Derived Ratios")
st.dataframe(hospital_derived_ratios_df)

st.subheader("Income Statement")
create_hierarchical_aggrid(hospital_df, ['Total Change in Unrestricted Net Assets'])

st.subheader("Balance Sheet")
create_hierarchical_aggrid(hospital_df, ['Total Unrestricted Assets', 'Total Liabilities and Equity'])

st.subheader("Balance Sheet Residuals (Children Sum - Parent)")
create_hierarchical_aggrid(hospital_residual_df, ['Total Unrestricted Assets', 'Total Liabilities and Equity'])

