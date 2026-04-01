import pandas as pd
import streamlit as st
from a_Config.enumerations.measure_source_enum import MeasureSource
from a_Config.global_constants import DERIVE_RATIOS, HOSPITAL_METADATA, SYSTEMS_TO_HOSPITALS_MAP, get_measure_tickformat
from a_Config.enumerations import *
from a_Config.fin_statement_model_utils import get_fin_statement_descendants_and_self
from c_Processing.c_main_data_pipeline import create_full_underived_df, to_dataset
from d_Transformations.derived_ratio_pipeline import run_derived_ratio_pipeline
from d_Transformations.dollar_level_pipeline import run_dollar_level_pipeline
from d_Transformations.normalize_measures import normalize_measures
from d_Transformations.aggregations import calc_population_aggregates
from e_Visualizations.hospital_time_series import plot_hospital_time_series
from e_Visualizations.aggrid_utils import create_hierarchical_aggrid, _tickformat_to_js

st.set_page_config(
    page_title="Individual Hospital Analysis",
    page_icon="🏥",
    layout="wide"
)


#######################################################################################################
# Cached pipeline helpers
#######################################################################################################

@st.cache_data
def _load_underived(states: tuple):
    return create_full_underived_df(list(states))


@st.cache_data
def _build_datasets(states: tuple, num_years_ma: int, entities: frozenset):
    df = _load_underived(states)
    df = df[df.index.get_level_values('Organization').isin(entities)]
    underived_ds = to_dataset(df)
    derived_ratio_ds = run_derived_ratio_pipeline(underived_ds, num_years_ma)
    dollar_level_ds = run_dollar_level_pipeline(underived_ds, num_years_ma)
    return dollar_level_ds, derived_ratio_ds


@st.cache_data
def _normalize_dollar_ds(_dollar_level_ds, normalization_measure: str):
    return normalize_measures(_dollar_level_ds, normalization_measure, vars=['value', 'ma'])


@st.cache_data
def _aggregate_normalized(_normalized_ds, active_var: str):
    return calc_population_aggregates(_normalized_ds, var=active_var)


#######################################################################################################
# User Inputs
#######################################################################################################

derived_ratios = list(DERIVE_RATIOS['Measure'].unique())
income_statement_items = list(get_fin_statement_descendants_and_self('Total Surplus/Deficit'))
balance_sheet_items = list(get_fin_statement_descendants_and_self('Total Unrestricted Assets') | get_fin_statement_descendants_and_self('Total Liabilities and Equity'))

selected_state = st.sidebar.selectbox('State', ['ME', 'MA'])

hospital_or_system = st.sidebar.segmented_control('', ['Hospital', 'System'], default='System', label_visibility='collapsed')

hospitals_in_state = sorted(org for org, state in HOSPITAL_METADATA.index if state == selected_state)
systems_in_state = sorted(system for (system, state) in SYSTEMS_TO_HOSPITALS_MAP if state == selected_state)
entities_in_state = sorted(set(hospitals_in_state) | set(systems_in_state))

type_entities = hospitals_in_state if hospital_or_system == 'Hospital' else systems_in_state

selected_entity = st.sidebar.selectbox(hospital_or_system, type_entities)

parent_system = next(
    (system for (system, state), hospitals in SYSTEMS_TO_HOSPITALS_MAP.items()
     if state == selected_state and selected_entity in hospitals),
    None
) if hospital_or_system == 'Hospital' else None

measure_source = st.sidebar.radio(
    'Measure Source',
    [e.value for e in MeasureSource]
)
measure_source = MeasureSource(measure_source)

match measure_source:
    case MeasureSource.RATIOS:
        measure_options = derived_ratios
    case MeasureSource.INCOME_STATEMENT:
        measure_options = income_statement_items
    case MeasureSource.BALANCE_SHEET:
        measure_options = balance_sheet_items

selected_measure = st.sidebar.selectbox('Measure', measure_options)

NORMALIZATION_OPTIONS = ['Total Unrestricted Assets', 'Total Revenue', 'Total Operating Revenue']

if measure_source != MeasureSource.RATIOS:
    normalization = st.sidebar.selectbox('Normalization', NORMALIZATION_OPTIONS)
else:
    normalization = None

endpoint_or_ma = MovingAvgOrEndpoint(
    st.sidebar.radio('Value Type', [e.value for e in MovingAvgOrEndpoint])
)

num_years_ma = st.sidebar.number_input('Lookback Years', 1, 10, 5)


#######################################################################################################
# Data
#######################################################################################################

dollar_level_ds, derived_ratio_ds = _build_datasets((selected_state,), num_years_ma, frozenset(entities_in_state))

if measure_source == MeasureSource.RATIOS:
    filtered_measure_ds = derived_ratio_ds
    active_var = 'ma' if endpoint_or_ma == MovingAvgOrEndpoint.MOVING_AVG else 'endpoint'
else:
    filtered_measure_ds = dollar_level_ds
    active_var = 'ma' if endpoint_or_ma == MovingAvgOrEndpoint.MOVING_AVG else 'value'

type_orgs = sorted(set(type_entities) & set(filtered_measure_ds.coords['organization'].values))
active_ds = filtered_measure_ds.sel(organization=type_orgs)

aggregate_ds = calc_population_aggregates(active_ds, var=active_var)

if measure_source != MeasureSource.RATIOS:
    full_normalized_ds = _normalize_dollar_ds(filtered_measure_ds, normalization)
    normalized_ds = full_normalized_ds.sel(organization=type_orgs)
    agg_norm_ds = _aggregate_normalized(normalized_ds, active_var)

#######################################################################################################
# Visualizations
#######################################################################################################

st.title(selected_entity)

###### Line Chart ######

show_normalized = False
if measure_source != MeasureSource.RATIOS:
    chart_col, toggle_col = st.columns([6.5, 1])
    with toggle_col:
        st.write("")
        show_normalized = st.toggle('Normalized')
else:
    chart_col = st.container()

chart_ds = normalized_ds if show_normalized else active_ds
chart_agg_ds = agg_norm_ds if show_normalized else aggregate_ds
hospital_da = chart_ds[active_var].sel(organization=selected_entity, state=selected_state, measure=selected_measure)
pop_mean_da = chart_agg_ds['mean'].sel(population='total', measure=selected_measure)
pop_std_da = chart_agg_ds['std'].sel(population='total', measure=selected_measure)
chart_tickformat = '.1%' if show_normalized else None

suffixes = [s for s in [
    '$' if (measure_source != MeasureSource.RATIOS and not show_normalized) else None,
    'Normalized' if show_normalized else None,
    f'{num_years_ma}yma' if endpoint_or_ma == MovingAvgOrEndpoint.MOVING_AVG else None,
] if s is not None]
title = f'{selected_measure} ({", ".join(suffixes)})' if suffixes else selected_measure

show_pop_band = measure_source == MeasureSource.RATIOS or show_normalized

with chart_col:
    st.plotly_chart(
        plot_hospital_time_series(
            hospital_da,
            pop_mean_da=pop_mean_da if show_pop_band else None,
            pop_std_da=pop_std_da if show_pop_band else None,
            hospital_name=selected_entity,
            measure=selected_measure,
            title=title,
            tickformat=chart_tickformat,
            yaxis_title=title,
        ),
        use_container_width=True,
    )

###### Measure Table ######

st.header('Data Exploration')

def _sel_series(da, name, decimals=3):
    return da.to_series().rename(name).round(decimals)

_, col = st.columns([7.5, 1])
with col:
    available_years = sorted((int(y) for y in active_ds.coords['year'].values), reverse=True)
    selected_year = st.selectbox('Year', available_years, index=0)

ds_measures = set(active_ds.coords['measure'].values)
table_measures = [m for m in measure_options if m in ds_measures]

hospital_vals = _sel_series(
    active_ds[active_var].sel(organization=selected_entity, state=selected_state, measure=table_measures, year=selected_year),
    'Value'
)

# TODO: This should really be refactored into a function
start_year = selected_year - num_years_ma
available_years_set = set(int(y) for y in active_ds.coords['year'].values)
if start_year in available_years_set:
    hospital_start_vals = _sel_series(
        active_ds[active_var].sel(organization=selected_entity, state=selected_state, measure=table_measures, year=start_year),
        '_start'
    )
    if measure_source == MeasureSource.RATIOS:
        change_col = ((hospital_vals - hospital_start_vals) / num_years_ma).rename('Ann. Change')
    else:
        change_col = ((hospital_vals / hospital_start_vals) ** (1 / num_years_ma) - 1).rename('Ann. % Change')
else:
    change_col = None

if measure_source != MeasureSource.RATIOS:
    extra_cols = [
        _sel_series(normalized_ds[active_var].sel(organization=selected_entity, state=selected_state, measure=table_measures, year=selected_year), f'Hospital / {normalization}'),
        *([_sel_series(full_normalized_ds[active_var].sel(organization=parent_system, state=selected_state, measure=table_measures, year=selected_year), parent_system)] if parent_system else []),
        _sel_series(agg_norm_ds['mean'].sel(population='total', measure=table_measures, year='Total'), f'Population / {normalization}'),
        _sel_series(agg_norm_ds['mean'].sel(population='failed', measure=table_measures, year='Total'), f'Failed / {normalization}'),
    ]
else:
    extra_cols = [
        *([_sel_series(filtered_measure_ds[active_var].sel(organization=parent_system, state=selected_state, measure=table_measures, year=selected_year), parent_system)] if parent_system else []),
        _sel_series(aggregate_ds['mean'].sel(population='total', measure=table_measures, year='Total'), 'Population Mean'),
        _sel_series(aggregate_ds['mean'].sel(population='failed', measure=table_measures, year='Total'), 'Failed Mean'),
    ]
change_cols = [change_col] if change_col is not None else []
table_df = hospital_vals.to_frame().join(change_cols + extra_cols)

if measure_source != MeasureSource.RATIOS:
    match measure_source:
        case MeasureSource.INCOME_STATEMENT:
            roots = ['Net Income']
        case MeasureSource.BALANCE_SHEET:
            roots = ['Total Unrestricted Assets', 'Total Liabilities and Equity']
    col_formatters = {table_df.columns[0]: _tickformat_to_js(get_measure_tickformat(table_measures[0])), **{col: _tickformat_to_js('.1%') for col in table_df.columns[1:]}}
    create_hierarchical_aggrid(table_df, roots=roots, col_formatters=col_formatters)
else:
    st.dataframe(table_df, use_container_width=True)


###### System Hospital Breakdown ######

if hospital_or_system == 'System':
    system_hospitals = sorted(SYSTEMS_TO_HOSPITALS_MAP.get((selected_entity, selected_state), set()))
    available_hospitals = [h for h in system_hospitals if h in filtered_measure_ds.coords['organization'].values]

    if available_hospitals:
        st.subheader(f'Hospitals in {selected_entity} — {selected_measure}')
        raw_vals = _sel_series(
            filtered_measure_ds[active_var].sel(
                organization=available_hospitals, state=selected_state, measure=selected_measure, year=selected_year
            ),
            'Value',
        )

        if measure_source != MeasureSource.RATIOS:
            norm_col = f'/ {normalization}'
            norm_vals = _sel_series(
                full_normalized_ds[active_var].sel(
                    organization=available_hospitals, state=selected_state, measure=selected_measure, year=selected_year
                ),
                norm_col,
            )
            hospital_table = raw_vals.to_frame().join(norm_vals)
            styled = hospital_table.style.format({'Value': '${:,.0f}', norm_col: '{:.1%}'})
        else:
            hospital_table = raw_vals.to_frame()
            styled = hospital_table.style

        st.dataframe(styled, use_container_width=True)

###### Data Dump ######

data_dump_expander = st.expander(f'All Hospital {measure_source.value} Data', expanded=False)

with data_dump_expander:
    st.caption('Download via the toolbar icon in the top-right corner of the table.')
    dump_df = active_ds[active_var].to_series().unstack('year')
    st.dataframe(dump_df, use_container_width=True)