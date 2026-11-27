from typing import NotRequired, TypedDict

# https://github.com/stac-extensions/themes/tree/v1.0.0
SCHEMA_URI = "https://stac-extensions.github.io/themes/v1.0.0/schema.json"



class ThemeConcept(TypedDict):
    id: str
    title: NotRequired[str]
    description: NotRequired[str]
    # RECOMMENDED. A URI providing further description of the concept.
    url: NotRequired[str]


class ThemeObject(TypedDict):
    # An identifier for the knowledge organization system used.
    # It is recommended that the identifier is a resolvable URI.
    scheme: str
    # One or more entity/concept identifers from this knowledge system.
    concepts: list[ThemeConcept]
