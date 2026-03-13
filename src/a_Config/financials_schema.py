import pandera as pa

financials_schema = pa.DataFrameSchema(
    index=pa.MultiIndex([
        pa.Index(str, name="Organization"),
        pa.Index(str, name="State"),
        pa.Index(str, name="Measure"),
        pa.Index(str, name="Endpoint or MA"),
        pa.Index(str, name="Raw or Derived"),
        pa.Index(int, name="Year"),
        ]),
    columns={
        'Year Failed': pa.Column(str, nullable=True),
        'Value': pa.Column(float, nullable=True),
    },
    strict=True,  # errors if unexpected columns
)