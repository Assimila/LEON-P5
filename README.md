# Land‑Use Intensity Data Pipeline

This repository contains scripts and notebooks for downloading, preprocessing, and classifying land-use related datasets to generate the Biodiversity Intactness Index (BII). The workflow integrates data from Google Earth Engine (GEE), the Copernicus Land Monitoring Service (CLMS), and the Global Human Settlement Layer (GHSL) to produce covariates and land-use intensity (LUI) classes. The PREDICTS database is then modelled and combined with the LUI outputs to generate the BII. Together, these components form a reproducible pipeline for deriving consistent, spatially explicit LUI and BII layers.

---


## Repository Structure

```txt
.
├── environment.yml
├── 0_download_viirs_gee.js
├── 0_download_natural_forest_gee.js
├── 0_download_modis-npp_gee.js
├── 0_download_clms.ipynb
├── 1_prep_raw_datasets.ipynb
├── 2_prep_covariates.ipynb
├── 3_class_land_use_intensity.ipynb
├── 4_calc_bii_predicts_world.R
└── 4_calc_bii_predicts_europe.R
```
---

## Workflow Overview

The analysis pipeline follows five main stages:

1. **Download raw datasets**
2. **Prepare and harmonise raw data**
3. **Generate covariates**
4. **Land‑use intensity classification**
5. **Biodiversity Intactness Index (BII) calculation**

Each step builds on the outputs of the previous one.

---

## 0 — Data Download

### Google Earth Engine (GEE)

The following JavaScript files are intended to be run in the **Google Earth Engine Code Editor**.

- **`0_download_viirs_gee.js`**  
  Downloads VIIRS night‑time lights data.

- **`0_download_natural_forest_gee.js`**  
  Downloads natural forest cover datasets.

- **`0_download_modis-npp_gee.js`**  
  Downloads MODIS Net Primary Productivity (NPP) data.

Data are exported from GEE (e.g. to Google Drive or Earth Engine Assets) for local processing.

---

### Copernicus Land Monitoring Service (CLMS)

- **`0_download_clms/`**  
  Jupyter notebook(s) using the Copernicus API to download CLMS products  
  (e.g. CLCplus Land Cover, Agriculture Layers).

Copernicus credentials are required to run these notebooks.

---

### Global Human Settlement Layer (GHSL)

GHSL datasets are **downloaded manually** from the official Copernicus GHSL homepage:

https://human-settlement.emergency.copernicus.eu/download.php

The following reference years are used:
- **2015**
- **2020**
- **2025**

Downloaded GHSL files are ingested and processed in subsequent preprocessing steps.

---

## 1 — Prepare Raw Datasets (Jupyter Notebooks)

- **`1_prep_raw_datasets/`**

Jupyter notebook(s) for cleaning and harmonising raw datasets, including:
- Unzipping and merging files
- Coordinate reference system (CRS) alignment
- Spatial resampling
- Clipping to the study area

Outputs from this step serve as standardised inputs for covariate generation.

---

## 2 — Prepare Covariates (Jupyter Notebooks)

- **`2_prep_covariates/`**

Jupyter notebook(s) deriving analysis‑ready covariates from the processed datasets, including:
- Fragmentation metrics
- Plantation classification
- Secondary vegetation classification
- Pasture classification
- Bare land total
- Grazing intensity

All covariates are aligned to a common grid and spatial extent.

---

## 3 — Land‑Use Intensity Classification (Jupyter Notebooks)

- **`3_class_land_use_intensity/`**

Jupyter notebook(s) for classifying land‑use intensity into **three classes** based on the prepared covariates.

---

## 4 — Biodiversity Intactness Index (BII) Calculation (R)

- **`4_calc_bii_predicts_world/`**

R script(s) for calculating the **Biodiversity Intactness Index (BII)** using:
- The PREDICTS global database
- Generated land‑use and land‑use intensity layers

- **`4_calc_bii_predicts_europe/`**

R script(s) for calculating the **Biodiversity Intactness Index (BII)** using:
- The PREDICTS european database
- Generated land‑use and land‑use intensity layers


This step is implemented entirely in **R**.

---

## Environment Setup

### Conda Environment

- **`environment.yml`**

Defines a reproducible Conda environment for all Python‑based preprocessing and analysis steps (Jupyter notebooks).

Create and activate the environment with:

```bash
conda env create -f environment.yml
conda activate <environment-name>