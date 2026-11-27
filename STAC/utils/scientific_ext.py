from typing import TypedDict

# https://github.com/stac-extensions/scientific/tree/v1.0.0
SCHEMA_URI = "https://stac-extensions.github.io/scientific/v1.0.0/schema.json"


class Publication(TypedDict):
    # The DOI of a publication referencing the data.
    # This MUST NOT be a DOIs link.
    doi: str
    # Citation of a publication referencing the data.
    citation: str
