import pandera as pa

financials_schema = pa.DataFrameSchema(
    index=pa.MultiIndex([
        pa.Index(str, name="Organization"),
        pa.Index(str, name="Measure"),
        ]),
    columns={
        'State': pa.Column(str),
        # Regex matches any 4-digit year column
        r"^\d{4}$": pa.Column(float, nullable=True, regex=True),
    },
    strict=True,  # errors if unexpected columns
)