import streamlit as st
import pandas as pd
import os
from b_Ingest.ingest_ratios import create_combined_financial_df
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode, GridUpdateMode
from a_Config.global_constants import FINANCIAL_STATEMENT_MODEL
from d_Visualizations.aggrid_utils import create_hierarchical_aggrid

# Page configuration
st.set_page_config(
    page_title="Hospital Financial Ratios",
    page_icon="🏥",
    layout="wide"
)

# Title
st.title("Maine Hospital Financial Ratios")

ingest_path = os.path.join(os.getcwd(), 'src', 'z_Data', 'Preprocessed_Data')
files = [
         'hospital_dollar_elements_2005_2009.csv',
         'hospital_dollar_elements_2010_2014.csv',
         'hospital_dollar_elements_2015_2019.csv',
         'hospital_dollar_elements_2020_2024.csv'
         ]
dollar_df = create_combined_financial_df(ingest_path, files, measure='Measure')

st.sidebar.header("Navigation")
selected_hospital = st.sidebar.selectbox(
    'Select Hospital',
    options=sorted(dollar_df.index.get_level_values('Hospital').unique().tolist()),
    index=0
)

hospital_df = dollar_df.xs(selected_hospital, level='Hospital')

st.subheader("Balance Sheet")
create_hierarchical_aggrid(hospital_df, ['Total Unrestricted Assets', 'Total Liabilities and Equity'])

st.subheader("Income Statement")
create_hierarchical_aggrid(hospital_df, ['Excess of Revenue Over Expenses'])
