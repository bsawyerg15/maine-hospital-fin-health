import streamlit as st
import pandas as pd
import sys
import os
from b_Ingest.ingest_ratios import create_combined_financial_df

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

# # Load data
# df = pd.read_pickle('hospital_ratios.pkl')

# Sidebar (temporarily hardcoded until ratios df loaded)
st.sidebar.header("Navigation")
selected_hospital = st.sidebar.selectbox('Select Hospital', options=dollar_df.index.get_level_values('Hospital').unique().tolist(), index=0)
# # selected_year = st.sidebar.selectbox('Year', options=['FY 2020', 'FY 2021', 'FY 2022', 'FY 2023', 'FY 2024'], index=4)
# # selected_columns = st.sidebar.multiselect('Ratios', options=df.index.get_level_values('Ratio').tolist(), default=['Total Margin', 'Operating Margin', 'Days Cash on Hand, Current days', 'Average Pay Period, Current Liabilities days'])

# # # Filter to selected year and pivot ratios as columns
# # filtered_df = df.reset_index()[['Hospital', 'Ratio', selected_year]]
# # pivoted_df = filtered_df.pivot(index='Hospital', columns='Ratio', values=selected_year)
# # pivoted_filtered_df = pivoted_df[selected_columns]

# # styled_df = pivoted_filtered_df.style.format("{:.2f}")

# Display the styled DataFrame
st.dataframe(dollar_df.xs(selected_hospital, level='Hospital'))
