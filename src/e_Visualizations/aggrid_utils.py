import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode, GridUpdateMode
from a_Config.global_constants import FINANCIAL_STATEMENT_MODEL


def create_hierarchical_aggrid(
    hospital_df: pd.DataFrame,
    roots: list[str],
    col_formatters: dict[str, str] | None = None,
    theme: str = "material",
):
    model = FINANCIAL_STATEMENT_MODEL
    subtree_measures = set()
    ancestor_prefixes = []
    for root in roots:
        root_path = model.loc[root, 'Path']
        root_mask = (model['Path'] == root_path) | model['Path'].str.startswith(root_path + ';')
        subtree_measures.update(model[root_mask].index)
        if ';' in root_path:
            ancestor_prefixes.append(root_path.rsplit(';', 1)[0] + ';')

    df = hospital_df.copy()
    df = df[df.index.isin(subtree_measures)].reset_index()
    df = df.merge(model[['Path']], left_on='measure', right_index=True, how='left')
    df['hierarchy_path'] = df['Path']
    df.drop('Path', axis=1, inplace=True)

    for prefix in ancestor_prefixes:
        mask = df['hierarchy_path'].str.startswith(prefix)
        df.loc[mask, 'hierarchy_path'] = df.loc[mask, 'hierarchy_path'].str[len(prefix):]

    columns = list(hospital_df.columns)

    column_defs = [
        {'field': 'hierarchy_path', 'hide': True}
    ]
    for col in columns:
        col_def = {
            'field': col,
            'headerName': col,
            'width': 120,
            'suppressSizeToFit': True,
            'type': 'numericColumn',
        }
        if col_formatters and col in col_formatters:
            col_def['valueFormatter'] = col_formatters[col]
        column_defs.append(col_def)

    gb = GridOptionsBuilder.from_dataframe(df)
    grid_options = gb.build()
    grid_options["columnDefs"] = column_defs

    grid_options["autoGroupColumnDef"] = {
        "headerName": "Measure",
        "minWidth": 350,
        "pinned": "left",
        "cellRendererParams": {
            "suppressCount": True,
        },
    }

    grid_options["treeData"] = True
    grid_options["animateRows"] = True
    grid_options["groupDefaultExpanded"] = 1
    grid_options["domLayout"] = "autoHeight"
    grid_options["getDataPath"] = JsCode("""
        function(data) {
            return data.hierarchy_path.split(";");
        }
    """).js_code

    return AgGrid(
        df,
        gridOptions=grid_options,
        allow_unsafe_jscode=True,
        enable_enterprise_modules=True,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        theme=theme,
        tree_data=True,
    )
