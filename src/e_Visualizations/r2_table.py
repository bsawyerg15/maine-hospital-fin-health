import numpy as np
import pandas as pd
import xarray as xr


def _r2(x: pd.Series, y: pd.Series) -> float:
    """R² of a linear fit of x vs y. Returns NaN if underdetermined."""
    df = pd.DataFrame({'x': x, 'y': y}).dropna()
    if len(df) < 3:
        return float('nan')
    coeffs = np.polyfit(df['x'], df['y'], 1)
    y_hat = np.polyval(coeffs, df['x'])
    ss_res = np.sum((df['y'] - y_hat) ** 2)
    ss_tot = np.sum((df['y'] - df['y'].mean()) ** 2)
    return 1 - ss_res / ss_tot if ss_tot > 0 else float('nan')


def calc_r2_table(
    interface_ds: xr.Dataset,
    selected_measure: str,
    measures: list[str],
    y_lag: int = 0,
) -> pd.DataFrame:
    """
    For each measure in *measures*, compute the R² of *selected_measure* vs
    that measure using both the ``last`` and ``ma`` data variables of
    *interface_ds*.

    Parameters
    ----------
    interface_ds : xr.Dataset
        Dataset with data variables ``last`` and ``ma``, each having dims
        ``(organization, state, measure, year)``.
    selected_measure : str
        The reference measure (x-axis in each bivariate regression).
    measures : list[str]
        Measures to compare against *selected_measure* (y-axis). The row for
        *selected_measure* itself will show R² = 1.
    y_lag : int
        Number of years to shift the x (selected_measure) series forward before
        computing R². Mirrors the lag applied in the scatter plot.

    Returns
    -------
    pd.DataFrame
        Columns: ``Measure`` (or ``Measure (lag Ny)``), ``Last R²``, ``MA R²``,
        sorted descending by ``Last R²``.
    """
    last_x_da = interface_ds['last'].sel(measure=selected_measure)
    ma_x_da = interface_ds['ma'].sel(measure=selected_measure)
    if y_lag != 0:
        last_x_da = last_x_da.shift(year=y_lag)
        ma_x_da = ma_x_da.shift(year=y_lag)
    last_x = last_x_da.to_series()
    ma_x = ma_x_da.to_series()

    rows = []
    for m in measures:
        last_y = interface_ds['last'].sel(measure=m).to_series()
        ma_y = interface_ds['ma'].sel(measure=m).to_series()
        rows.append({
            'Measure': m,
            'Last R²': _r2(last_x, last_y),
            'MA R²': _r2(ma_x, ma_y),
        })

    df = pd.DataFrame(rows).sort_values('Last R²', ascending=False, ignore_index=True).round({'Last R²': 2, 'MA R²': 2})
    if y_lag != 0:
        lag_sign = '+' if y_lag > 0 else ''
        df = df.rename(columns={'Measure': f'Measure (lag {lag_sign}{y_lag}y)'})
    return df
