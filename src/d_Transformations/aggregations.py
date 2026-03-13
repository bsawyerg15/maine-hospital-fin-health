import pandas as pd
import xarray as xr
from a_Config.global_constants import HOSPITAL_METADATA


def create_mean_df(ds: xr.Dataset, var: str = 'endpoint') -> xr.DataArray:
    """
    Returns the mean Value across organizations for each (measure, year).

    Args:
        ds: Financials Dataset with 'endpoint' and 'ma' variables.
        var: Which variable to average ('endpoint' or 'ma').

    Returns:
        DataArray with dims (state, measure, year).
    """
    return ds[var].mean(dim='organization')


def create_failed_dataset(ds: xr.Dataset, num_years: int = 6) -> xr.Dataset:
    """
    Filters to failed hospitals and returns a Dataset indexed by relative_year
    instead of year (0 = failure year, -1 = one year prior, etc.).

    Args:
        ds: Full financials Dataset with 'endpoint', 'ma', and 'year_failed'.
        num_years: How many years before (and including) failure to keep.

    Returns:
        Dataset with dims (organization, measure, relative_year). Missing
        relative_year slots for hospitals with fewer available years are
        filled with NaN via outer join on concat. State is carried as a
        non-dimension coordinate on the organization dimension.
    """
    failed_metadata = HOSPITAL_METADATA[HOSPITAL_METADATA['Year Failed'].notna()]
    all_orgs = set(ds.coords['organization'].values)
    all_states = set(ds.coords['state'].values)
    all_years = sorted(int(y) for y in ds.coords['year'].values)

    slices = []
    orgs = []
    states_out = []

    for (hospital, state), row in failed_metadata.iterrows():
        if hospital not in all_orgs or state not in all_states:
            continue

        year_failed = int(row['Year Failed'])
        selected = [y for y in all_years if y <= year_failed][-num_years:]
        if not selected:
            continue

        relative = [y - year_failed for y in selected]

        h_ds = xr.Dataset({
            var: (
                ds[var]
                .sel(organization=hospital, state=state, year=selected)
                .assign_coords(year=relative)
                .rename({'year': 'relative_year'})
            )
            for var in ('endpoint', 'ma')
        })
        slices.append(h_ds)
        orgs.append(hospital)
        states_out.append(state)

    if not slices:
        return xr.Dataset()

    combined = xr.concat(
        slices,
        dim=pd.Index(orgs, name='organization'),
        join='outer',
    )
    return combined.assign_coords(state=('organization', states_out))


def filter_to_non_failed(ds: xr.Dataset) -> xr.Dataset:
    """
    Masks all organizations that have a non-null year_failed with NaN.
    """
    return ds.where(ds['year_failed'].isnull())
