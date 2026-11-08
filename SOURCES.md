# Data Sources

## 1. Main Dataset

**Organization:** Centers for Disease Control and Prevention (CDC)

**Dataset name:** Behavioral Risk Factor Surveillance System (BRFSS), 2022 Annual Data

**File used:** LLCP2022ASC.zip

**Extracted file:** LLCP2022.ASC

**Format:** Fixed-width ASCII data

**Official dataset download URL:**
https://www.cdc.gov/brfss/annual_data/2022/files/LLCP2022ASC.zip

**BRFSS 2022 annual data page:**
https://www.cdc.gov/brfss/annual_data/annual_2022.html

**Local acquisition record:** 24 October 2026 (based on the local archive file timestamp).

The ZIP archive and extracted dataset are stored in `data/` and excluded from Git because of their size.

## 2. Additional CDC Documentation

**Diabetes optional module – 2022:**
https://www.cdc.gov/brfss/questionnaires/modules/category2022.htm

**BRFSS questionnaires:**
https://www.cdc.gov/brfss/questionnaires/

## 3. Variable Layout Documentation

Local documentation: `docs/variable_layout.html`

| Variable | Description |
|---|---|
| DIABETE4 | Diabetes status |
| DIABTYPE | Diabetes type |
| _AGEG5YR | Age category |
| _BMI5CAT | BMI category |

## 4. Dataset Integrity

The project records the SHA-256 checksum in:

`checksums/LLCP2022ASC.zip.sha256`

Recorded SHA-256:

`ce4e8453afd8685977a13e56da85418eff83e628547604b00e3463eb60c2fc74`

This checksum was calculated locally from the project archive. It is used to verify the local file's integrity and is not presented as an official CDC checksum.

The pipeline verifies the archive before extraction and analysis.

## 5. Data Usage

The dataset is used for an academic exploratory analysis of Type 2 diabetes in relation to age and BMI categories.

Please consult the official CDC website for dataset documentation and applicable terms of use.
