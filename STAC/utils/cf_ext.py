from typing import NotRequired, TypedDict

# https://github.com/stac-extensions/cf/tree/v0.2.0
SCHEMA_URI = "https://stac-extensions.github.io/cf/v0.2.0/schema.json"

class CFObject(TypedDict):
    # non-empty value from the CF standard names list
    # https://cfconventions.org/Data/cf-standard-names/current/build/cf-standard-name-table.html
    name: str
    # Indicates the unit, preferably available in the database from the UDUNITS-2 package (unidata)
    # https://docs.unidata.ucar.edu/udunits/current/
    unit: NotRequired[str]
