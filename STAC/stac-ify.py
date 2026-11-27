"""
Create a STAC catalogue for the LEON Pilot 5 output experimental dataset (BII and LUI),
for inclusion in the ESA Project Results Repository (PRR).
"""

import datetime
import os
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

import pystac
import rasterio as rio
import utils
from pystac.extensions.classification import Classification
from pystac.layout import CustomLayoutStrategy
from rio_cogeo.cogeo import cog_validate
from rio_stac.stac import create_stac_item

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "data"
STAC_DIR = SCRIPT_DIR / "STAC"
DESCRIPTIONS_DIR = SCRIPT_DIR / "descriptions"
THUMBNAILS_DIR = SCRIPT_DIR / "thumbnails"
THUMBNAIL_NAME = "thumbnail.jpg"
FILENAME_RE = re.compile(
    r"^(?P<product>bii|lui)_(?P<country>[a-z]{3})_(?P<year>\d{4})_(?P<version>v\d+)$"
)

CATALOG_ID = "leon-p5"
CATALOG_TITLE = "LEON Pilot 5 - Natural Capital and Economic Accounting"
CATALOG_DESCRIPTION = (
    "Output experimental dataset of LEON Pilot 5: land-use intensity (LUI) and "
    "predicted Biodiversity Intactness Index (BII) for Denmark and the Netherlands, 2018-2023."
)
KEYWORDS = []  # TODO

LICENSE = "CC-BY-NC-4.0"

OSC_PROJECT = "LEON"
OSC_PROJECT_DESCRIPTION = (DESCRIPTIONS_DIR / "LEON.md").read_text()
OSC_PROJECT_WEBSITE = "https://www.leon-naturefinance.org/"
OSC_INITIATIVE = "apex"
OSC_CONTRACT_NUMBER = "4000146275/24/I-NS"
# OSC_VARIABLES = ["Land use intensity", "Biodiversity intactness index"]
OSC_MISSIONS = ["PLACEHOLDER"]  # TODO

PROCESSING_DATETIME = datetime.datetime(
    2026, 1, 1, tzinfo=datetime.timezone.utc
)  # TODO

SCIENTIFIC_PUBLICATIONS: list[utils.scientific_ext.Publication] = []  # TODO

TEMPORAL_START = datetime.datetime(2018, 1, 1, tzinfo=datetime.timezone.utc)
TEMPORAL_END = datetime.datetime(
    2023, 12, 31, 23, 59, 59, tzinfo=datetime.timezone.utc
)


# Allowed themes in the PRR are
# `athmosphere`,`cryosphere`,`land`,`magntosphere-ionosphere`,`oceans`,`solid-earth`
THEMES: list[utils.themes_ext.ThemeObject] = [
    utils.themes_ext.ThemeObject(
        # scheme as instructed by https://github.com/stac-extensions/osc/tree/v1.0.0#themes
        scheme="https://github.com/stac-extensions/osc#theme",
        concepts=[
            utils.themes_ext.ThemeConcept(
                id="land",
            )
        ],
    )
]


# TODO
CF_PARAMETER: list[utils.cf_ext.CFObject] = [
    utils.cf_ext.CFObject(
        name="area_type",
    )
]


LUI_CLASSES: list[Classification] = [
    Classification.create(value=0, name="nodata", title="No data", nodata=True),
    Classification.create(
        value=1, name="urban_minimal", title="Urban, minimal", color_hint="D9A196"
    ),
    Classification.create(
        value=2, name="urban_light", title="Urban, light", color_hint="D97360"
    ),
    Classification.create(
        value=3, name="urban_intense", title="Urban, intense", color_hint="D93F23"
    ),
    Classification.create(
        value=4, name="crop_minimal", title="Crop, minimal", color_hint="D4C894"
    ),
    Classification.create(
        value=5, name="crop_light", title="Crop, light", color_hint="D4BE5F"
    ),
    Classification.create(
        value=6, name="crop_intense", title="Crop, intense", color_hint="D4B21D"
    ),
    Classification.create(
        value=7, name="pasture_minimal", title="Pasture, minimal", color_hint="B183C9"
    ),
    Classification.create(
        value=8, name="pasture_light", title="Pasture, light", color_hint="A35BC9"
    ),
    Classification.create(
        value=9, name="pasture_intense", title="Pasture, intense", color_hint="8E1EC9"
    ),
    Classification.create(
        value=10,
        name="plantation_minimal",
        title="Plantation, minimal",
        color_hint="F2C8A7",
    ),
    Classification.create(
        value=11,
        name="plantation_light",
        title="Plantation, light",
        color_hint="F2A76A",
    ),
    Classification.create(
        value=12,
        name="plantation_intense",
        title="Plantation, intense",
        color_hint="F28329",
    ),
    Classification.create(
        value=13,
        name="secondary_vegetation_indeterminate_age_minimal",
        title="Secondary vegetation, indeterminate age, minimal",
        color_hint="AAD994",
    ),
    Classification.create(
        value=14,
        name="secondary_vegetation_indeterminate_age_light",
        title="Secondary vegetation, indeterminate age, light",
        color_hint="87D960",
    ),
    Classification.create(
        value=15,
        name="secondary_vegetation_indeterminate_age_intense",
        title="Secondary vegetation, indeterminate age, intense",
        color_hint="61D928",
    ),
    Classification.create(
        value=16,
        name="secondary_vegetation_young_minimal",
        title="Secondary vegetation, young, minimal",
        color_hint="95BD81",
    ),
    Classification.create(
        value=17,
        name="secondary_vegetation_young_light",
        title="Secondary vegetation, young, light",
        color_hint="76BD54",
    ),
    Classification.create(
        value=18,
        name="secondary_vegetation_young_intense",
        title="Secondary vegetation, young, intense",
        color_hint="55BD23",
    ),
    Classification.create(
        value=19,
        name="secondary_vegetation_intermediate_minimal",
        title="Secondary vegetation, intermediate, minimal",
        color_hint="5A724E",
    ),
    Classification.create(
        value=20,
        name="secondary_vegetation_intermediate_light",
        title="Secondary vegetation, intermediate, light",
        color_hint="487233",
    ),
    Classification.create(
        value=21,
        name="secondary_vegetation_intermediate_intense",
        title="Secondary vegetation, intermediate, intense",
        color_hint="337215",
    ),
    Classification.create(
        value=22,
        name="secondary_vegetation_mature_minimal",
        title="Secondary vegetation, mature, minimal",
        color_hint="43543A",
    ),
    Classification.create(
        value=23,
        name="secondary_vegetation_mature_light",
        title="Secondary vegetation, mature, light",
        color_hint="345425",
    ),
    Classification.create(
        value=24,
        name="secondary_vegetation_mature_intense",
        title="Secondary vegetation, mature, intense",
        color_hint="26540F",
    ),
]

# TODO
PROVIDERS: list[pystac.Provider] = [
    pystac.Provider(
        name="Assimila",
        roles=[pystac.ProviderRole.PROCESSOR],
        url="https://www.assimila.earth/",
    ),
]


def copy_collection_thumbnail(product: str) -> None:
    """Copy a collection thumbnail from thumbnails/ into STAC/{product}/"""
    src = THUMBNAILS_DIR / f"{product}.jpg"
    out_path = STAC_DIR / product / THUMBNAIL_NAME
    out_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, out_path)


@dataclass(frozen=True)
class FileInfo:
    product: str
    country: str
    year: int
    version: str


def parse_stem(path: Path) -> FileInfo:
    """
    Converts a filename like `bii_dnk_2018_v7.tif` into a FileInfo object.
    """
    match = FILENAME_RE.match(path.stem)
    if match is None:
        print(
            f"Unexpected file name {path.name}, expected {FILENAME_RE.pattern}",
            file=sys.stderr,
        )
        sys.exit(1)
    groups = match.groupdict()
    return FileInfo(
        product=groups["product"].upper(),
        country=groups["country"],
        year=int(groups["year"]),
        version=groups["version"],
    )


def check_cog(path: Path):
    is_valid, errors, warnings = cog_validate(path, quiet=True)
    if not is_valid:
        print(f"NOT A VALID COG: {path}")
    for error in errors:
        print(f"> ERROR: {error}")
    for warning in warnings:
        print(f"> WARNING: {warning}")


def spatial_resolution_meters(
    dataset: rio.DatasetReader,
) -> float:
    """Get the spatial resolution in meters from a rasterio dataset."""
    crs = dataset.crs
    if crs is None or not crs.is_projected:
        raise ValueError("expected a projected CRS with metre-like spacing")
    a, b, _, d, e, _ = dataset.transform[:6]  # noqa: RUF059
    if b != 0 or d != 0:
        raise ValueError("grid is rotated or sheared")
    x_res, y_res = dataset.res
    unit, metres_per_unit = crs.linear_units_factor  # noqa: RUF059
    return ((x_res + y_res) / 2) * metres_per_unit


def build_item(
    tif_path: Path,
    band_name: str,
    classes: list[Classification] | None = None,
) -> pystac.Item:
    file_info = parse_stem(tif_path)

    asset_href = f"../../../data/{tif_path.relative_to(DATA_DIR).as_posix()}"
    start = datetime.datetime(file_info.year, 1, 1, tzinfo=datetime.timezone.utc)
    end = datetime.datetime(
        file_info.year, 12, 31, 23, 59, 59, tzinfo=datetime.timezone.utc
    )

    with rio.open(tif_path) as dataset:
        # we use rio-stac to scaffold a STAC Item
        # but rio-stac is hard-coded to older STAC extensions
        item = create_stac_item(
            source=dataset,
            id=tif_path.stem,
            input_datetime=start,
            asset_roles=["data"],
            asset_href=asset_href,
            with_proj=True,
            with_raster=True,
            with_eo=False,
        )
        spatial_resolution = spatial_resolution_meters(dataset)

    item = utils.migrate_stac_item.migrate_stac_item(item)

    # set temporal infomation to a time range
    item.datetime = None
    item.common_metadata.start_datetime = start
    item.common_metadata.end_datetime = end

    (asset,) = item.assets.values()
    (band,) = asset.extra_fields["bands"]

    # STAC-REC-05 - asset title
    asset.title = tif_path.stem

    # STAC-REC-05 - asset file:size, file:checksum
    asset.ext.add("file")
    asset.ext.file.size = tif_path.stat().st_size  # units: bytes
    asset.ext.file.checksum = utils.checksum.sha256_multihash(tif_path)

    # STAC-REC-08 - band name
    band["name"] = band_name

    # STAC-REC-10 - raster:spatial_resolution
    band["raster:spatial_resolution"] = spatial_resolution

    # STAC-REC-12 - classification extension for categorical data
    if classes is not None:
        asset.ext.add("classification")
        asset.ext.classification.apply(classes=classes)

    return item


def build_collection(
    *,
    collection_id: str,
    collection_title: str,
    band_name: str,
    osc_variables: list[str],
    deferred: utils.defer_assignment.DeferAssignment,
    classes: list[Classification] | None = None,
) -> pystac.Collection:
    collection = pystac.Collection(
        id=collection_id,
        title=collection_title,
        description=(DESCRIPTIONS_DIR / f"{collection_id}.md").read_text(),
        # extent will be updated later
        extent=pystac.Extent(
            spatial=pystac.SpatialExtent([[-180.0, -90.0, 180.0, 90.0]]),
            temporal=pystac.TemporalExtent([[TEMPORAL_START, TEMPORAL_END]]),
        ),
        license=LICENSE,
        keywords=KEYWORDS,
        providers=PROVIDERS,
    )

    # MUST contain at least one asset named `thumbnail` with `thumbnail` role
    copy_collection_thumbnail(collection_id)
    collection.add_asset(
        "thumbnail",
        pystac.Asset(
            href=f"./{THUMBNAIL_NAME}",
            media_type=pystac.MediaType.JPEG,
            roles=["thumbnail"],
        ),
    )

    # REQUIRED A list of extension identifiers the Collection implements.
    # Must contain the following extensions: OSC, Scientific, Processing, Themes, CF
    collection.stac_extensions.append(utils.osc_ext.SCHEMA_URI)
    collection.stac_extensions.append(utils.scientific_ext.SCHEMA_URI)
    collection.stac_extensions.append(utils.processing_ext.SCHEMA_URI)
    collection.stac_extensions.append(utils.themes_ext.SCHEMA_URI)
    collection.stac_extensions.append(utils.cf_ext.SCHEMA_URI)

    # OSC extension
    collection.extra_fields["osc:type"] = "product"  # I guess "product", not "project"
    collection.extra_fields["osc:status"] = "completed"
    collection.extra_fields["osc:project"] = OSC_PROJECT
    deferred(
        collection.extra_fields, "osc:project_description", OSC_PROJECT_DESCRIPTION
    )
    deferred(collection.extra_fields, "osc:project_website", OSC_PROJECT_WEBSITE)
    deferred(collection.extra_fields, "osc:initiative", OSC_INITIATIVE)
    deferred(collection.extra_fields, "osc:contract-number", OSC_CONTRACT_NUMBER)
    collection.extra_fields["osc:variables"] = osc_variables
    deferred(collection.extra_fields, "osc:missions", OSC_MISSIONS)

    # Scientific extension
    collection.extra_fields["sci:publications"] = SCIENTIFIC_PUBLICATIONS

    # Processing extension
    # "processing:" fields are not recognised on a Collection
    # so put in Collection summaries as well.
    collection.extra_fields["processing:datetime"] = PROCESSING_DATETIME.isoformat()
    collection.summaries.add("processing:datetime", [PROCESSING_DATETIME.isoformat()])
    # processing:version is optional

    # Themes extension
    collection.extra_fields["themes"] = THEMES

    # CF extension
    collection.extra_fields["cf:parameter"] = CF_PARAMETER

    # 🐛 cf extension v0.2.0 bug 🐛
    # json schema for collection summaries uses `oneOf`, not `anyOf`.
    # If it matches 2+ conditions it fails!
    # The workaround is to set "cf:parameter" on collection summaries as well.
    collection.summaries.add("cf:parameter", CF_PARAMETER)

    tif_paths = sorted((DATA_DIR / collection_id).glob("*.tif"))
    for tif_path in tif_paths:
        print(f"processing {tif_path}")
        check_cog(tif_path)
        item = build_item(tif_path, band_name=band_name, classes=classes)
        collection.add_item(item)

    collection.update_extent_from_items()
    return collection


def stac_item_href(item: pystac.Item, parent_dir: str) -> str:
    """Path for each Item JSON when normalizing the STAC tree.

    Puts every item under an `items/` subfolder next
    to `collection.json`, named `{item.id}.json`.

    Args:
        item: The STAC Item
        parent_dir: Absolute directory of the parent Collection on disk

    Returns:
        Absolute path to `items/<item.id>.json` under `parent_dir`.
    """
    return os.path.join(parent_dir, "items", f"{item.id}.json")


def main() -> None:
    # clean up everything in STAC_DIR
    for path in STAC_DIR.glob("*"):
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()

    STAC_DIR.mkdir(parents=True, exist_ok=True)

    # PRR Collections Specifications requires OSC extension v1.0.0
    # but also requires some "osc:" fields that are forbidden by the extension schema!
    deferred = utils.defer_assignment.DeferAssignment()

    # root catalogue
    root = pystac.Catalog(
        id=CATALOG_ID,
        title=CATALOG_TITLE,
        description=CATALOG_DESCRIPTION,
        catalog_type=pystac.CatalogType.SELF_CONTAINED,
    )

    # LUI collection
    lui = build_collection(
        collection_id="LUI",
        collection_title="Land Use Intensity (LUI)",
        band_name="LUI",
        osc_variables=["Land use intensity"],
        deferred=deferred,
        classes=LUI_CLASSES,
    )
    root.add_child(lui)

    # BII collection
    bii = build_collection(
        collection_id="BII",
        collection_title="Biodiversity Intactness Index (BII)",
        band_name="BII",
        osc_variables=["Biodiversity intactness index"],
        deferred=deferred,
    )
    root.add_child(bii)

    root.normalize_hrefs(
        str(STAC_DIR), strategy=CustomLayoutStrategy(item_func=stac_item_href)
    )
    root.validate_all()
    deferred.apply()
    root.save()


if __name__ == "__main__":
    main()
