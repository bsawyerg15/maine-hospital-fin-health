import xarray as xr


def normalize_measures(ds: xr.Dataset, measure_name: str, vars: list = None) -> xr.Dataset:
    """
    Divides data variables in ds by the corresponding value of measure_name,
    aligned on (organization, state, year). Each variable is normalized by itself
    (e.g. 'ma' is divided by the 'ma' value of measure_name, 'value' by its 'value').

    Args:
        ds: xarray Dataset with dims (organization, state, measure, year).
        measure_name: The measure to normalize by. Must be present in ds.
        vars: Data variables to normalize. Defaults to all variables in ds.

    Returns:
        Dataset with the same structure, each variable divided by the selected measure.
        The normalizing measure itself is retained (will be all 1.0s).
        Returns an empty Dataset if measure_name is not found.
    """
    if measure_name not in ds.coords['measure'].values:
        return xr.Dataset()

    target_vars = vars if vars else list(ds.data_vars)
    return ds.assign({var: ds[var] / ds[var].sel(measure=measure_name) for var in target_vars})
