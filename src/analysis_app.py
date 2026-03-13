import streamlit as st
from a_Config.global_constants import DERIVE_RATIOS
from c_Processing.c_main_data_pipeline import create_full_underived_df, to_dataset
from d_Transformations.aggregations import create_failed_dataset
from d_Transformations.transformation_pipeline import run_transformation_pipeline
from e_Visualizations.failed_histogram import plot_failed_histogram
from e_Visualizations.mean_bar_charts import plot_mean_bar_chart
from e_Visualizations.leadup_to_failure import plot_leadup_to_failure


#######################################################################################################
# User Inputs
#######################################################################################################

selected_date = st.sidebar.selectbox(
    'Analysis Period End',
    options=['Total'] + sorted([str(i) for i in range(2000, 2025)], reverse=True),
    index=0
)

num_years_ma = st.sidebar.number_input(
    'Number of Years Before Failing',
    1, 10, 5
)

selected_states = st.sidebar.multiselect(
    'States', ['ME', 'MA'], default=['ME']
)

#######################################################################################################
# Data
#######################################################################################################

underived_df = create_full_underived_df(selected_states)
ds = run_transformation_pipeline(to_dataset(underived_df), num_years_ma)
failed_ds = create_failed_dataset(ds, num_years_ma + 1)

#######################################################################################################
# Viz
#######################################################################################################

st.set_page_config(
    page_title="Hospital Cross-Sectional Analysis",
    page_icon="🏥",
    layout="wide"
)

st.title("What are the financial characteristics of failed hospitals?")

#######################################################################################################
# Intro Charts
#######################################################################################################

margin = 0.3
_, col, side_col = st.columns([0.1, 1, margin])

derived_measures = list(DERIVE_RATIOS['Measure'].unique())

with side_col:
    selected_measure = st.selectbox('Measure', derived_measures, 2)
    is_use_ma_for_hist = st.radio('', ['Endpoint', 'Moving Avg']) == 'Moving Avg'

non_failed_da = ds['endpoint'].sel(measure=selected_measure).where(ds['year_failed'].isnull())
non_failed_mean = float(non_failed_da.mean())
non_failed_std_dev = float(non_failed_da.std())

with col:
    st.plotly_chart(
        plot_failed_histogram(
            ds,
            failed_ds,
            selected_measure,
            ma_years=num_years_ma if is_use_ma_for_hist else None,
        ),
        use_container_width=True
    )

col1, _, col2 = st.columns([1, 0.2, 2])

with col1:
    st.plotly_chart(
        plot_mean_bar_chart(
            [
                non_failed_da.values.flatten(),
                failed_ds['endpoint'].sel(measure=selected_measure, relative_year=0).values.flatten(),
                failed_ds['ma'].sel(measure=selected_measure, relative_year=-1).values.flatten(),
            ],
            ['Operational', 'Failed Year', f'{num_years_ma}yma Before Failing'],
            title=f'Mean {selected_measure} +/- 1 Std. Dev.',
        )
    )

with col2:
    st.plotly_chart(
        plot_leadup_to_failure(
            failed_ds['endpoint'].sel(measure=selected_measure),
            non_failed_mean,
            non_failed_std_dev,
            yaxis_title=selected_measure,
            title=f'Lead Up to Failure vs Population: {selected_measure}',
        )
    )
