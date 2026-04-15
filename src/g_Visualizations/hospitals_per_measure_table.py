import streamlit as st
import xarray as xr
from pandas.io.formats.style import Styler

from a_Config.global_constants import get_measure_tickformat


def hospitals_per_measure_table(active_ds: xr.Dataset, selected_measure: str, last_col: str, ma_col: str, num_years_ma: int, chart_format=None) -> Styler:
    available_years = sorted(int(y) for y in active_ds.coords['year'].values)
    selected_table_year = st.select_slider('Year', options=available_years, value=available_years[-1])

    table_df = active_ds.sel(measure=selected_measure, year=selected_table_year).to_dataframe()[[last_col, ma_col]].dropna().sort_values(last_col, ascending=False)
    
    fmt = chart_format
    table_df.columns = [f'{selected_measure}', f'{selected_measure}, {num_years_ma}yma']
    table_df.index.names = ['Organization', 'State']
    if fmt.startswith('$'):
        formatter = lambda x: f'${x:{fmt[1:]}}'
    else:
        formatter = '{:' + fmt + '}'
    return table_df.style.format(formatter)
