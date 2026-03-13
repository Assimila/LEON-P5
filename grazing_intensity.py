"""
Grazing Intensity — Relative Stocking Density (RSD)
Following Piipponen et al. (2022) using MODIS NPP.
"""

import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling
from pathlib import Path


# ── Configuration ────────────────────────────────────────────────────────────

# Livestock AU conversion factors
AU_FACTORS = {"cattle": 1.0, "sheep": 0.1, "goat": 0.1, "horse": 0.8}

# Tree cover exponential decay coefficient
TREE_DECAY = 4.45521

# fANPP regression coefficients (Hui & Jackson 2006)
FANPP_INTERCEPT = 0.171
FANPP_SLOPE = 0.0129

# Carbon-to-biomass conversion
CARBON_FACTOR = 0.485

# Animal Unit annual intake (kg/AU/yr)
AU_WEIGHT = 455          # kg
AU_DAILY_INTAKE = 0.025  # fraction of body weight
AU_ANNUAL_INTAKE = AU_WEIGHT * AU_DAILY_INTAKE * 365  # ~4156 kg


# ── Helpers ──────────────────────────────────────────────────────────────────

def _reproject_to_grid(src_path, dst_shape, dst_transform, dst_crs,
                       resampling=Resampling.bilinear):
    """Reproject a single-band raster onto the NPP reference grid."""
    out = np.full(dst_shape, np.nan, dtype="float32")
    with rasterio.open(src_path) as src:
        reproject(
            source=rasterio.band(src, 1),
            destination=out,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=dst_transform,
            dst_crs=dst_crs,
            src_nodata=src.nodata,
            dst_nodata=np.nan,
            resampling=resampling,
        )
    return out


def _tree_cover_fraction(lc_path, tree_classes, dst_shape, dst_transform,
                         dst_crs, max_dim=5000):
    """Read land-cover, build tree mask, reproject as fractional coverage."""
    with rasterio.open(lc_path) as src:
        factor = max(1, int(np.ceil(max(src.height, src.width) / max_dim)))
        lc = src.read(
            1,
            out_shape=(src.height // factor, src.width // factor),
            resampling=Resampling.mode,
        )
        mask = np.isin(lc, tree_classes).astype("float32")
        ds_transform = src.transform * src.transform.scale(factor, factor)

        frac = np.zeros(dst_shape, dtype="float32")
        reproject(
            source=mask,
            destination=frac,
            src_transform=ds_transform,
            src_crs=src.crs,
            dst_transform=dst_transform,
            dst_crs=dst_crs,
            resampling=Resampling.average,
        )
    return np.clip(frac, 0, 1)


# ── Main routine ─────────────────────────────────────────────────────────────

def compute_rsd(
    npp_path: Path,
    temp_path: Path,
    lc_path: Path,
    livestock_paths: dict[str, Path],
    out_path: Path,
    tree_cover_classes: list[int] = (2, 3, 4),
    country: str = "",
):
    """
    Compute Relative Stocking Density and write to GeoTIFF.

    Parameters
    ----------
    npp_path           : Path to MODIS NPP raster (g C m⁻² yr⁻¹).
    temp_path          : Path to mean annual temperature raster (°C).
    lc_path            : Path to land-cover raster (CLC+ or similar).
    livestock_paths    : Dict with keys 'cattle','sheep','goat','horse'
                         mapping to headcount rasters.
    out_path           : Destination GeoTIFF for the RSD layer.
    tree_cover_classes : Pixel values representing tree canopy.
    country            : ISO-3 country code (used for goat override).
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # 1 ── Reference grid (NPP) ──────────────────────────────────────────────
    with rasterio.open(npp_path) as src:
        npp = src.read(1).astype("float32")
        profile = src.profile.copy()
        transform = src.transform
        crs = src.crs
    shape = npp.shape

    # 2 ── Temperature → fANPP ────────────────────────────────────────────────
    mat = _reproject_to_grid(temp_path, shape, transform, crs,
                             resampling=Resampling.bilinear)
    f_anpp = FANPP_INTERCEPT + FANPP_SLOPE * mat  # NaN where temp is NaN

    # 3 ── Tree cover → multiplier ────────────────────────────────────────────
    tcf = _tree_cover_fraction(lc_path, list(tree_cover_classes),
                               shape, transform, crs)
    tree_mult = 1.0 / np.exp(TREE_DECAY * tcf)

    # 4 ── Above-ground biomass → carrying capacity ──────────────────────────
    agb = (npp * f_anpp / CARBON_FACTOR) * tree_mult   # g/m²/yr
    agb_kg_km2 = agb * 1e3                              # kg/km²/yr
    cc = agb_kg_km2 / AU_ANNUAL_INTAKE                   # AU/km²

    # 5 ── Livestock → Animal Units ───────────────────────────────────────────
    au = np.zeros(shape, dtype="float32")
    for species, path in livestock_paths.items():
        density = _reproject_to_grid(path, shape, transform, crs,
                                     resampling=Resampling.average)
        au += np.nan_to_num(density) * AU_FACTORS[species]

    # 6 ── Relative Stocking Density ──────────────────────────────────────────
    rsd = np.full(shape, np.nan, dtype="float32")
    valid = (npp > 0) & np.isfinite(cc) & (cc > 0) & (au >= 0)
    rsd[valid] = au[valid] / cc[valid]

    # 7 ── Write output ───────────────────────────────────────────────────────
    profile.update(dtype="float32", compress="lzw")
    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(rsd, 1)

    print(f"✅  {out_path.name}  —  "
          f"min={np.nanmin(rsd):.3f}  mean={np.nanmean(rsd):.3f}  "
          f"median={np.nanmedian(rsd):.3f}  max={np.nanmax(rsd):.3f}")
    return rsd


# ── CLI entry point ──────────────────────────────────────────────────────────

if __name__ == "__main__":

    # === EDIT THESE =========================================================
    BASE = Path("~/data/LEON_P5_BII").expanduser()
    COUNTRY = "nld"
    YEARS = [2019, 2020, 2021]
    TREE_CLASSES = [2, 3, 4]
    # ========================================================================

    for year in YEARS:
        print(f"\n── {COUNTRY.upper()} {year} {'─'*50}")
        compute_rsd(
            npp_path=BASE / f"EO_data_prep/Modis_NPP/NPP_{COUNTRY}_{year}_clip.tif",
            temp_path=BASE / f"EO_data_prep/Temp_avg/wc2.1_2.5m_tavg_{COUNTRY}_mean_annual.tif",
            lc_path=BASE / f"EO_data_prep/CLCplus/clcplus_{COUNTRY}_{year}.tif",
            livestock_paths={
                "cattle": BASE / f"EO_data_prep/Lifestock_GPW/gpw_cattle.headcount.faostat_rf_m_1km_s_{COUNTRY}_{year}_clip.tif",
                "sheep":  BASE / f"EO_data_prep/Lifestock_GPW/gpw_sheep.headcount.faostat_rf_m_1km_s_{COUNTRY}_{year}_clip.tif",
                "goat":   BASE / f"EO_data_prep/Lifestock_GPW/gpw_goat.headcount.faostat_rf_m_1km_s_{COUNTRY}_{year}_clip.tif",
                "horse":  BASE / f"EO_data_prep/Lifestock_GPW/gpw_horse.headcount.faostat_rf_m_1km_s_{COUNTRY}_{year}_clip.tif",
            },
            out_path=BASE / f"EO_data_prep/Grazing_intensity/RSD_{COUNTRY}_{year}.tif",
            tree_cover_classes=TREE_CLASSES,
            country=COUNTRY,
        )