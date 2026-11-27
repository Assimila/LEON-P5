Land-use intensity (LUI) for Denmark and the Netherlands for the years 2018–2023, produced by LEON Pilot 5 (Natural Capital and Economic Accounting).

The LUI layers provide a spatially explicit representation of land-use classes and their associated management intensity, following the PREDICTS land-use and land-use-intensity framework (Hudson et al., 2014). Each pixel is assigned a land-use type (e.g. cropland, pasture, plantation, secondary vegetation, urban) and one of three management intensity levels: minimal, light or intense. The layers are derived from yearly-updated Earth observation products, mainly from the Copernicus Land Monitoring Service (CLMS), and are the input to the pilot's Biodiversity Intactness Index (BII) predictions.

## Data

- One single-band GeoTIFF per country and year, named `lui_<ISO3 country code>_<year>_<version>`, e.g. `lui_dnk_2018_v7`.
- Data type `uint8`, categorical; nodata is `0`.
- CRS EPSG:3035 (ETRS89-extended / LAEA Europe).

## Classes

| Land use | minimal | light | intense |
| --- | --- | --- | --- |
| Urban | 1 | 2 | 3 |
| Crop | 4 | 5 | 6 |
| Pasture | 7 | 8 | 9 |
| Plantation | 10 | 11 | 12 |
| Secondary vegetation, indeterminate age | 13 | 14 | 15 |
| Secondary vegetation, young | 16 | 17 | 18 |
| Secondary vegetation, intermediate | 19 | 20 | 21 |
| Secondary vegetation, mature | 22 | 23 | 24 |

## Known limitations

- CLMS products are consistently available only from 2018 onward and only for Europe.
- Some PREDICTS land-use descriptions, such as hunting pressure or fertiliser type, cannot be observed from Earth observation data.
- The Natural Forest 2020 dataset, used to separate plantation forest from secondary vegetation, is a single snapshot and is treated as static over 2018–2023.
- Forest structural stages (young to mature) are distinguished using tree cover density, which is a proxy for canopy development rather than a direct measure of forest structure.
- Cropland intensity uses bare-soil days and small woody features as proxies. Where bare-soil observations are missing, a uniform 90 bare-soil days is assumed.
- Urban intensity thresholds on population density were calibrated visually on Danish landscapes.
