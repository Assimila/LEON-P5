import pystac
from packaging.version import Version
from pystac.extensions.base import VERSION_REGEX

# https://github.com/stac-extensions/raster
RASTER_EXT_ROOT = "https://stac-extensions.github.io/raster"
RASTER_EXT_V2 = f"{RASTER_EXT_ROOT}/v2.0.0/schema.json"


# mapping from v1 key -> v2 key
RASTER_EXT_VERSION_MAPPING = {
    "sampling": "raster:sampling",
    "bits_per_sample": "raster:bits_per_sample",
    "spatial_resolution": "raster:spatial_resolution",
    "scale": "raster:scale",
    "offset": "raster:offset",
    "histogram": "raster:histogram",
    # moved from raster extension to common metadata band object in STAC v1.1.0
    "nodata": "nodata",
    "data_type": "data_type",
    "statistics": "statistics",
    "unit": "unit",
}


def migrate_stac_item(item: pystac.Item) -> pystac.Item:
    """
    Invoke pystac internal migration logic,
    to update the versions of STAC and STAC extensions.
    """
    # pystac internal migration logic
    item = pystac.Item.from_dict(item.to_dict(), migrate=True)

    # we're waiting for https://github.com/stac-utils/pystac/pull/1829 👀

    # if raster extension < v2.0.0
    if item.ext.has("raster"):
        do_migrate = False
        for uri in item.stac_extensions:
            if uri.startswith(RASTER_EXT_ROOT):
                version_str = (
                    VERSION_REGEX.search(uri).group(0).strip("/")
                )  # e.g. "v1.1.0"
                if Version(version_str) < Version("v2.0.0"):
                    do_migrate = True

        if do_migrate:
            # print("Migrating raster extension to v2.0.0")
            item.ext.remove("raster")
            item.stac_extensions.append(RASTER_EXT_V2)

            for asset in item.assets.values():
                raster_bands = asset.extra_fields.pop("raster:bands", [])
                if "bands" not in asset.extra_fields:
                    # list of band objects
                    asset.extra_fields["bands"] = [{} for _ in raster_bands]

                for band_obj, raster_band in zip(
                    asset.extra_fields["bands"], raster_bands
                ):
                    for v1_key, v2_key in RASTER_EXT_VERSION_MAPPING.items():
                        if v1_key in raster_band and v2_key not in band_obj:
                            band_obj[v2_key] = raster_band[v1_key]

    return item
