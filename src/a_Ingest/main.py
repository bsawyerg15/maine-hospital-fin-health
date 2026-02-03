import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Page configuration
st.set_page_config(
    page_title="Hospital Financial Ratios",
    page_icon="🏥",
    layout="wide"
)

# Title
st.title("Maine Hospital Financial Ratios")

# Load data
df = pd.read_pickle('../../hospital_ratios.pkl')

# Sidebar
st.sidebar.header("Navigation")
selected_year = st.sidebar.selectbox('Year', options=['FY 2020', 'FY 2021', 'FY 2022', 'FY 2023', 'FY 2024'], index=4)
selected_columns = st.sidebar.multiselect('Ratios', options=df.index.get_level_values('Ratio').tolist(), default=['Total Margin', 'Operating Margin', 'Days Cash on Hand, Current days', 'Average Pay Period, Current Liabilities days'])

# Filter to selected year and pivot ratios as columns
filtered_df = df.reset_index()[['Hospital', 'Ratio', selected_year]]
pivoted_df = filtered_df.pivot(index='Hospital', columns='Ratio', values=selected_year)
pivoted_filtered_df = pivoted_df[selected_columns]

styled_df = pivoted_filtered_df.style.format("{:.2f}")

# Display the styled DataFrame
st.dataframe(styled_df)
