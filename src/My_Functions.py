import pandas as pd


@pd.api.extensions.register_dataframe_accessor('filter_multiindex')
class FilterMultiindexAccessor:
    """
    Registered as df.filter_multiindex(...).

    Filter a MultiIndex DataFrame by cross-sectioning on specified levels,
    leaving others intact. Fails if any index level is not accounted for
    in filters or untouched, making new index levels immediately visible.

    Parameters
    ----------
    filters : list of (key, level_name)
        Each tuple specifies the value to select and the level to filter via xs.
        Applied iteratively in order.
    untouched : list of str
        Index level names that should pass through unmodified.

    Raises
    ------
    ValueError
        If any index level is not accounted for in filters or untouched.
    KeyError
        If a level name in filters or untouched does not exist in the index.

    Example
    -------
    df.filter_multiindex([('Maine', 'State'), (2023, 'Year')], untouched=['Hospital'])
    """

    def __init__(self, df: pd.DataFrame):
        self._df = df

    def __call__(
        self,
        filters: list[tuple[any, str]],
        untouched: list[str],
    ) -> pd.DataFrame:
        index_names = set(self._df.index.names)
        filter_levels = {level for _, level in filters}
        untouched_set = set(untouched)

        unaccounted = index_names - filter_levels - untouched_set
        if unaccounted:
            raise ValueError(
                f"Index levels not accounted for in filters or untouched: {unaccounted}. "
                f"Add them to filters or untouched to make the intent explicit."
            )

        unknown_filter_levels = filter_levels - index_names
        if unknown_filter_levels:
            raise KeyError(f"Filter levels not found in index: {unknown_filter_levels}")

        unknown_untouched = untouched_set - index_names
        if unknown_untouched:
            raise KeyError(f"Untouched levels not found in index: {unknown_untouched}")

        result = self._df
        for key, level in filters:
            result = result.xs(key, level=level)

        return result
