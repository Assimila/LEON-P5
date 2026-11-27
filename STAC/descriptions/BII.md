Predicted Biodiversity Intactness Index (BII) for Denmark and the Netherlands for the years 2018-2023, produced by LEON Pilot 5 (Natural Capital and Economic Accounting).

The BII is defined as "the average abundance of a large and diverse set of organisms in a given geographical area, relative to their reference populations" (Scholes and Biggs, 2005). It is an abundance-weighted index of diversity relative to the reference state: a value close to 1 indicates that an area is close to biodiversity intactness, where the naturally occurring biodiversity of the pristine state largely remains. The modelled BII combines two metrics, both relative to the pristine reference state: total abundance, and compositional similarity to the reference measured by the balanced Bray-Curtis index.

BII is predicted from the pilot's land-use intensity (LUI) proportions and statistical models fitted to the PREDICTS database, following De Palma et al. (2024) and extended to cover all LUI classes. Minimally used primary vegetation is the reference. The layers in this collection use the models estimated with the full, global PREDICTS database.

## Data

- One single-band GeoTIFF per country and year, named `bii_<ISO3 country code>_<year>_<version>`, e.g. `bii_dnk_2018_v7`.
- Data type `float32`; nodata is `NaN`.
- CRS EPSG:3035 (ETRS89-extended / LAEA Europe).

## Interpretation

Following Steffen et al. (2015), a BII below 0.3 is categorised as high risk, 0.3–0.9 as within the zone of uncertainty, and at least 0.9 as below the boundary (safe).

## Known limitations

- Land-use intensity alone explains a small part of the variance in total abundance (ca. 2.3%) and community composition (ca. 8.4%, together with geographic distance between sites). The layers therefore represent expected BII given land-use intensity, with large unmodelled site-level variance, and BII should not be used as the sole biodiversity indicator.
- The PREDICTS database covers terrestrial biodiversity only; freshwater and marine biodiversity are not considered.
- Some regions are much better represented in PREDICTS than others.
