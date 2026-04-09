import pandas as pd
import xarray as xr
from a_Config.enumerations.change_or_level_enum import ChangeOrLevel
from a_Config.enumerations.interface_fields_enum import InterfaceFields


def run_combined_pipeline(level_ds: xr.Dataset, change_ds: xr.Dataset) -> xr.Dataset:
    """
    Merge level and change datasets into a single Dataset with a
    ``change_or_level`` dimension.

    Both input datasets are normalized to the same two data variables
    (``InterfaceFields.ENDPOINT`` and ``InterfaceFields.MA``) before
    concatenation:
      - level_ds already exposes endpoint / ma → kept as-is.
      - change_ds exposes change / ma_of_change / cum_change →
        change → endpoint, ma_of_change → ma, cum_change dropped.

    The ``year_failed`` coordinate is preserved from ``level_ds``.

    Args:
        level_ds:  Dataset produced by run_level_pipeline.
        change_ds: Dataset produced by run_change_pipeline.

    Returns:
        Dataset with dims (organization, state, measure, year, change_or_level)
        and data variables InterfaceFields.ENDPOINT and InterfaceFields.MA.
    """
    level_normed = xr.Dataset(
        {
            InterfaceFields.ENDPOINT: level_ds[InterfaceFields.ENDPOINT],
            InterfaceFields.MA: level_ds[InterfaceFields.MA],
        },
        coords={'year_failed': level_ds['year_failed']},
    )

    change_normed = xr.Dataset(
        {
            InterfaceFields.ENDPOINT: change_ds[InterfaceFields.CHANGE],
            InterfaceFields.MA: change_ds[InterfaceFields.MA_OF_CHANGE],
        },
        coords={'year_failed': change_ds['year_failed']},
    )

    return xr.concat(
        [level_normed, change_normed],
        dim=pd.Index([ChangeOrLevel.LEVEL, ChangeOrLevel.CHANGE], name='change_or_level'),
    )
