import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode, GridUpdateMode
from a_Config.global_constants import FINANCIAL_STATEMENT_MODEL

def create_hierarchical_aggrid(hospital_df: pd.DataFrame, roots: list[str], height: int = 400, theme: str = "material"):
    model = FINANCIAL_STATEMENT_MODEL
    subtree_measures = set()
    for root in roots:
        root_mask = (model['Path'] == root) | model['Path'].str.startswith(root + '/')
        subtree_measures.update(model[root_mask].index)

    df = hospital_df[hospital_df.index.isin(subtree_measures)].reset_index()
    df = df.merge(model[['Path']], left_on='Measure', right_index=True, how='left')
    df['hierarchy_path'] = df['Path']
    df.drop('Path', axis=1, inplace=True)

    years = list(hospital_df.columns)

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
    grid_options["getDataPath"] = JsCode("""
        function(data) {
            return data.hierarchy_path.split("/");
        }
    """).js_code

    return AgGrid(
        df,
        gridOptions=grid_options,
        height=height,
        allow_unsafe_jscode=True,
        enable_enterprise_modules=True,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        theme=theme,
        tree_data=True,
    )
