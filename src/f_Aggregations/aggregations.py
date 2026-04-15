import numpy as np
import pandas as pd
import xarray as xr
from a_Config.global_constants import HOSPITAL_METADATA
from a_Config.enumerations import ChangeType

def calc_aggregates(ds: xr.Dataset, var: str, change_type: ChangeType = ChangeType.ARITHMETIC, year_dim: str = 'year') -> xr.Dataset:
    """
    Returns the mean and standard deviation of a variable, broken out by year
    plus a 'Total' entry pooling all years.

    Args:
        ds: Financials Dataset.
        var: Which variable to aggregate.
        change_type: If GEOMETRIC, compute via log(1+x) transform.
        year_dim: Name of the time dimension to break out by. Use 'year' for
            the full dataset and 'relative_year' for failed-hospital datasets.

    Returns:
        Dataset with 'mean' and 'std' variables, each with dims (measure, year_dim).
        The year_dim coordinate contains all values present in ds plus the string
        'Total' (all years pooled).
    """
    if not ds.data_vars or ds[var].sizes.get('measure', 1) == 0:
        year_vals = list(ds.coords[year_dim].values) + ['Total'] if year_dim in ds.coords else ['Total']
        empty = xr.DataArray(np.empty((0, len(year_vals))), dims=['measure', year_dim],
                             coords={'measure': np.array([], dtype=object), year_dim: year_vals})
        return xr.Dataset({'mean': empty, 'std': empty})

    is_geometric = change_type == ChangeType.GEOMETRIC
    data = ds[var]
    if is_geometric:
        data = np.log1p(data)

    obs_dims = [d for d in data.dims if d not in ('measure', year_dim)]
    per_year = data.stack(obs=obs_dims)
    per_year_mean = per_year.mean(dim='obs')
    per_year_std = per_year.std(dim='obs')

    total = data.stack(obs=[*obs_dims, year_dim])
    total_mean = total.mean(dim='obs').expand_dims({year_dim: ['Total']})
    total_std = total.std(dim='obs').expand_dims({year_dim: ['Total']})

    if is_geometric:
        per_year_mean, per_year_std = np.expm1(per_year_mean), np.expm1(per_year_std)
        total_mean, total_std = np.expm1(total_mean), np.expm1(total_std)

    per_year_ds = xr.Dataset({'mean': per_year_mean, 'std': per_year_std})
    total_ds = xr.Dataset({'mean': total_mean, 'std': total_std})
    return xr.concat([per_year_ds, total_ds], dim=year_dim)


# TODO: refactor this to take a list of vars. should only have one agg ds
def calc_population_aggregates(ds: xr.Dataset, var: str, change_type: ChangeType = ChangeType.ARITHMETIC) -> xr.Dataset:
    """
    Runs calc_aggregates for three populations and returns them combined along
    a new 'population' dimension with values 'total', 'failed', 'non_failed'.

    Returns:
        Dataset with 'mean' and 'std' variables, each with dims (population, measure, year).
    """
    populations = {
        'total': ds,
        'failed': ds.where(ds['year_failed'].notnull()),
        'non_failed': filter_to_non_failed(ds),
    }
    return xr.concat(
        [calc_aggregates(pop_ds, var, change_type) for pop_ds in populations.values()],
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
        Dataset with dims (organization, state, measure, relative_year), matching
        the structure of the full dataset. Missing relative_year slots for hospitals
        with fewer available years are filled with NaN via outer join on concat.
    """
    failed_metadata = HOSPITAL_METADATA[HOSPITAL_METADATA['Year Failed'].notna()]
    all_orgs = set(ds.coords['organization'].values)
    all_states = set(ds.coords['state'].values)
    all_years = sorted(int(y) for y in ds.coords['year'].values)

    slices = []

    for (hospital, state), row in failed_metadata.iterrows():
        if hospital not in all_orgs or state not in all_states:
            continue

        year_failed = int(row['Year Failed'])
        target_years = set(range(year_failed - num_years + 1, year_failed + 1))
        selected = sorted(y for y in all_years if y in target_years)
        if not selected:
            continue

        relative = [y - year_failed for y in selected]

        full_relative_years = list(range(-(num_years - 1), 1))
        h_ds = xr.Dataset({
            var: (
                ds[var]
                .sel(organization=[hospital], state=[state], year=selected)
                .assign_coords(year=relative)
                .rename({'year': 'relative_year'})
            )
            for var in ds.data_vars
        }).reindex(relative_year=full_relative_years)
        slices.append(h_ds)

    if not slices:
        return xr.Dataset()

    return xr.concat(slices, dim='organization', join='outer')


def filter_to_non_failed(ds: xr.Dataset) -> xr.Dataset:
    """
    Masks all organizations that have a non-null year_failed with NaN.
    """
    return ds.where(ds['year_failed'].isnull())