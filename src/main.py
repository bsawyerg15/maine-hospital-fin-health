import streamlit as st
import pandas as pd
import os
from b_Ingest.ingest_me_financials import create_combined_me_financial_df
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode, GridUpdateMode
from a_Config.global_constants import FINANCIAL_STATEMENT_MODEL
from d_Visualizations.aggrid_utils import create_hierarchical_aggrid
from c_Processing.b_sum_of_children import calculate_residuals
from c_Processing.c_main_data_pipeline import process_financial_df


# Page configuration
st.set_page_config(
    page_title="Hospital Financial Ratios",
    page_icon="🏥",
    layout="wide"
)

# Title
st.title("Maine Hospital Financial Ratios")

dollar_df = process_financial_df('MA')

residual_df = calculate_residuals(dollar_df)


st.sidebar.header("Navigation")
selected_organization = st.sidebar.selectbox(
    'Select Organization',
    options=sorted(dollar_df.index.get_level_values('Organization').unique().tolist()),
    index=0
)

hospital_df = dollar_df.xs(selected_organization, level='Organization')
hospital_residual_df = residual_df.xs(selected_organization, level='Organization')


st.subheader("Balance Sheet")
create_hierarchical_aggrid(hospital_df, ['Total Unrestricted Assets', 'Total Liabilities and Equity'])

st.subheader("Balance Sheet Residuals (Children Sum - Parent)")
create_hierarchical_aggrid(hospital_residual_df, ['Total Unrestricted Assets', 'Total Liabilities and Equity'])

st.subheader("Income Statement")
create_hierarchical_aggrid(hospital_df, ['Excess of Revenue Over Expenses'])

