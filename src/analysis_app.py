import streamlit as st
import pandas as pd
import os
from b_Ingest.ingest_me_financials import create_combined_me_financial_df
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode, GridUpdateMode
from a_Config.global_constants import FINANCIAL_STATEMENT_MODEL
from d_Visualizations.aggrid_utils import create_hierarchical_aggrid
from c_Processing.b_sum_of_children import calculate_residuals
from c_Processing.c_main_data_pipeline import process_financial_df


st.title("Cross Sectional Analysis")