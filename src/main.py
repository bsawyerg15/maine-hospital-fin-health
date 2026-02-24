import streamlit as st
import pandas as pd
import os
from b_Ingest.ingest_ratios import create_combined_financial_df
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode, GridUpdateMode
from a_Config.global_constants import FINANCIAL_STATEMENT_MODEL

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
years = list(hospital_df.columns)

roots = ['Total Unrestricted Assets', 'Total Liabilities and Equity']

model = FINANCIAL_STATEMENT_MODEL
subtree_measures = set()
for root in roots:
    root_mask = (model['Path'] == root) | model['Path'].str.startswith(root + '/')
    subtree_measures.update(model[root_mask].index)


df = hospital_df[hospital_df.index.isin(subtree_measures)].reset_index()
df = df.merge(model[['Path']], left_on='Measure', right_index=True, how='left')
df['hierarchy_path'] = df['Path']
df.drop('Path', axis=1, inplace=True)

# Configure AgGrid for row grouping tree
column_defs = [
    {'field': 'hierarchy_path', 'hide': True}
]

for year in years:
    column_defs.append({
        'field': year,
        'headerName': year,
        'valueFormatter': """params => {
            const val = params.value;
            if (val == null || isNaN(val)) return '';
            return '$' + Math.round(val).toLocaleString('en-US');
        }""",
        'type': 'numericColumn'
    })


gb = GridOptionsBuilder.from_dataframe(df)

grid_options = gb.build()

grid_options["columnDefs"] = column_defs

grid_options["autoGroupColumnDef"] = {
    "headerName": "Measure",
    "minWidth": 300,
    "cellRendererParams": {
        "suppressCount": True,
    },
}

grid_options["treeData"] = True
grid_options["animateRows"] = True
grid_options["groupDefaultExpanded"] = 1
grid_options["getDataPath"] = JsCode(
    """
    function(data) {
        return data.hierarchy_path.split("/");
    }
    """
).js_code

AgGrid(
    df,
    gridOptions=grid_options,
    height=400,
    allow_unsafe_jscode=True,     # needed for getDataPath JsCode
    enable_enterprise_modules=True,
    update_mode=GridUpdateMode.SELECTION_CHANGED,
    theme="material",
    tree_data=True,               # must also be True here
)
