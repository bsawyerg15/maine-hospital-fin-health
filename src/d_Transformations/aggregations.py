import numpy as np
import pandas as pd
import xarray as xr
from a_Config.global_constants import HOSPITAL_METADATA
from a_Config.enumerations import ChangeType

def calc_aggregates(ds: xr.Dataset, var: str = 'endpoint', is_geometric: bool = False) -> xr.Dataset:
    """
    Returns the mean and standard deviation of a variable, collapsed across
    all organizations and years into a single pool of points.

    Args:
        ds: Financials Dataset.
        var: Which variable to aggregate.
        is_geometric: If True, compute geometric mean and geometric standard
            deviation via log(1+x) transform, then exp(result)-1 to return
            to the original scale.

    Returns:
        Dataset with 'mean' and 'std' variables, each with dim (measure,).
    """
    stacked = ds[var].stack(obs=('organization', 'state', 'year'))
    if is_geometric:
        stacked = np.log1p(stacked)
    mean = stacked.mean(dim='obs')
    std = stacked.std(dim='obs')
    if is_geometric:
        mean, std = np.expm1(mean), np.expm1(std)
    return xr.Dataset({'mean': mean, 'std': std})


def calc_population_aggregates(ds: xr.Dataset, var: str = 'endpoint', change_type: ChangeType = ChangeType.ARITHMETIC) -> xr.Dataset:
    """
    Runs calc_aggregates for three populations and returns them combined along
    a new 'population' dimension with values 'total', 'failed', 'non_failed'.

    Returns:
        Dataset with 'mean' and 'std' variables, each with dims (population, measure).
    """
    populations = {
        'total': ds,
        'failed': ds.where(ds['year_failed'].notnull()),
        'non_failed': filter_to_non_failed(ds),
    }
    is_geometric = change_type == ChangeType.GEOMETRIC
    return xr.concat(
        [calc_aggregates(pop_ds, var, is_geometric) for pop_ds in populations.values()],
        dim=pd.Index(list(populations.keys()), name='population'),
    )



def create_failed_dataset(ds: xr.Dataset, num_years: int) -> xr.Dataset:
    """
    Filters to failed hospitals and returns a Dataset indexed by relative_year
    instead of year (0 = failure year, -1 = one year prior, etc.).

    Args:
        ds: Full financials Dataset.
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
            for var in ds.data_vars
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