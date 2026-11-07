# Enquête sur une maladie — Type 2 Diabetes Analysis

## 1. Project Overview

This project explores Type 2 diabetes using data from the 2022 Behavioral Risk Factor Surveillance System (BRFSS), published by the Centers for Disease Control and Prevention (CDC).

The main objective is to study descriptive relationships between Type 2 diabetes, age groups, and Body Mass Index (BMI) categories.

The project uses Bash, AWK, Python, Pandas, and Matplotlib to process a large fixed-width dataset, calculate descriptive statistics, and produce graphical visualizations.

The work follows a reproducible data-analysis workflow, from inspecting the original dataset to generating and validating summary files.

## 2. Research Objectives

The project has the following objectives:

- Explore diabetes-related responses in the BRFSS 2022 dataset.
- Distinguish respondents classified as having Type 2 diabetes from respondents reporting no diabetes.
- Examine the distribution of classified Type 2 diabetes cases across age groups.
- Compare BMI-category distributions between the two diabetes groups.
- Explore the relationship between age groups, BMI categories, and Type 2 diabetes.
- Produce CSV summaries and graphical visualizations.
- Reproduce an existing analysis using different programming tools.
- Document the methodology, limitations, and interpretation of the results.

This is a descriptive exploratory study. It does not aim to establish causal relationships.

## 3. Dataset

The project uses the CDC BRFSS 2022 ASCII dataset.

Official download:

https://www.cdc.gov/brfss/annual_data/2022/files/LLCP2022ASC.zip

The downloaded archive is:

`data/LLCP2022ASC.zip`

The extracted dataset is:

`data/LLCP2022.ASC`

The dataset contains approximately 445,132 respondent records. Each record is stored using a fixed-width format, with a record length of approximately 2,052 characters.

Unlike a CSV file, the ASCII dataset does not separate its variables using commas. Each variable is stored at a documented character position.

The raw dataset and ZIP archive are excluded from Git because of their size. To reproduce the analyses, download the archive from the official CDC source, extract it, and place the ASCII file inside the `data/` directory.

## 4. Tools and Technologies

- **Git Bash / Bash** — command-line navigation, file management, and data exploration.
- **AWK** — extracting fields from fixed-width records and calculating descriptive summaries.
- **Python** — data processing, validation, and visualization.
- **Pandas** — reading, filtering, grouping, and comparing datasets.
- **NumPy** — numerical computing support.
- **Matplotlib** — generating graphical visualizations.
- **Git and GitHub** — version control and project management.

## 5. Data Preparation and Variables

### 5.1 Fixed-width data format

The original BRFSS ASCII file uses fixed-width records.

The positions of the variables were identified using the CDC variable layout documentation:

`docs/variable_layout.html`

The main variables used in the project are:

| Variable   | Description                   |
| ---------- | ----------------------------- |
| `DIABETE4` | Diabetes status               |
| `DIABTYPE` | Diabetes type                 |
| `_AGEG5YR` | Age group                     |
| `_BMI5`    | Calculated BMI value          |
| `_BMI5CAT` | BMI category                  |
| `_RFBMI5`  | BMI-related derived indicator |

The Python implementation uses the following zero-based character intervals to extract the main fields:

| Field      | Character interval |
| ---------- | ------------------ |
| State code | `(0, 2)`           |
| `DIABETE4` | `(128, 129)`       |
| `DIABTYPE` | `(270, 271)`       |
| `_AGEG5YR` | `(1980, 1982)`     |
| `_BMI5CAT` | `(2001, 2002)`     |

These intervals follow Python's slicing convention: the starting position is included and the ending position is excluded.

### 5.2 Diabetes classification

For the main comparison, the project uses the following response classification:

- **Type 2 diabetes:** `DIABETE4 = 1` and `DIABTYPE = 2`.
- **No diabetes:** `DIABETE4 = 3`.

Other responses, including other diabetes classifications, unknown responses, refused responses, and missing values, are excluded from this two-group comparison.

These classifications must be interpreted according to the official CDC questionnaire and codebook.

### 5.3 Age and BMI categories

For the age-stratified analysis:

- Age codes `01` to `13` are retained.
- Age code `14` and other values are excluded.

For the age-and-BMI analysis, the following BMI category codes are retained:

- `1`
- `2`
- `3`
- `4`

Only records satisfying the selected state, age, BMI, and diabetes-group criteria are included in the corresponding comparison.

### 5.4 Selected states

The age-and-BMI analysis uses the following state or territory codes:

`10, 13, 18, 23, 28, 29, 32, 38, 45, 46, 50, 55, 78`

The full dataset contains 445,132 records. The selected codes account for 92,432 records.

The reason for selecting this subset and its relationship to diabetes-type data availability must be documented and validated against the official CDC documentation before making population-level interpretations.

## 6. Analysis Workflow

### 6.1 Bash and AWK exploration

Bash and AWK were used to explore and process the original ASCII dataset.

The work included:

- Inspecting the dataset's record length and number of records.
- Examining diabetes response codes.
- Exploring missing diabetes-type responses.
- Investigating state and territory coverage.
- Counting respondents by age group and BMI category.
- Calculating descriptive percentages.
- Checking the consistency of calculated percentages.
- Identifying groups with fewer than 20 classified Type 2 diabetes cases.

### 6.2 Age and diabetes

Output:

`results/age_diabetes.csv`

This file contains an age-group summary of respondents classified as having Type 2 diabetes and respondents classified as having no diabetes.

It provides a descriptive comparison of the two groups across age categories.

### 6.3 BMI and diabetes

Output:

`results/bmi_diabetes_comparison.csv`

This file compares the distribution of BMI categories between the classified Type 2 diabetes and no-diabetes groups.

It contains the group, BMI category, count, percentage, and total number of valid BMI records used for the corresponding group.

### 6.4 Age, BMI, and diabetes

Output:

`results/age_bmi_diabetes.csv`

This file combines age groups and BMI categories to examine their relationship with classified Type 2 diabetes.

Each row represents one age-and-BMI combination and contains:

- `age_code`: age-group code.
- `bmi_category`: BMI category.
- `type2_count`: number of classified Type 2 diabetes cases.
- `no_diabetes_count`: number of respondents classified as having no diabetes.
- `total`: total number of records in the two groups.
- `percentage`: descriptive Type 2 diabetes percentage.
- `small_case_count`: indicates whether the Type 2 diabetes count is below 20.

The percentage is calculated as:

`Type 2 cases / (Type 2 cases + No-diabetes cases) × 100`

This percentage describes the proportion of Type 2 diabetes cases among the two included groups within each age-and-BMI combination.

It is not an estimate of diabetes prevalence in the entire BRFSS population.

### 6.5 Python reproduction and validation

The age-and-BMI analysis was reproduced using Python and Pandas.

The Python implementation reads the original fixed-width dataset in chunks rather than loading the entire dataset into memory.

This approach reduces memory usage when processing the large ASCII file.

Python output:

`results/age_bmi_diabetes_python.csv`

The Python-generated CSV was compared with the original AWK-generated file:

`results/age_bmi_diabetes.csv`

Both files contained 52 age-and-BMI groups and produced identical values.

The comparison confirmed consistency between the two implementations for:

- Type 2 diabetes counts.
- No-diabetes counts.
- Total records.
- Calculated percentages.
- Small-group indicators.

This validation confirms that the Python implementation reproduces the AWK results. It does not independently validate the scientific classification rules, variable definitions, or sampling methodology.

## 7. Results Summary

During the Python processing of the complete dataset, the following counts were obtained using the current selection criteria:

| Description                                    |   Count |
| ---------------------------------------------- | ------: |
| Total dataset records                          | 445,132 |
| Records in selected states or territories      |  92,432 |
| Records included in the age-and-BMI comparison |  76,519 |
| Classified Type 2 diabetes cases               |   9,393 |
| Respondents classified as having no diabetes   |  67,126 |
| Age-and-BMI groups                             |      52 |

These figures describe the records retained by the project's current filters. They should not be interpreted as official CDC prevalence estimates.

## 8. Visualizations

Python, Pandas, and Matplotlib are used to generate the project's graphical visualizations.

### 8.1 Obesity and age

Output:

`results/obesity_age.png`

Generated by:

`scripts/plot_obesity_age.py`

This graph explores the descriptive Type 2 diabetes percentage across age groups within BMI category 4 (obesity).

Groups with fewer than 20 classified Type 2 diabetes cases are excluded from this visualization.

### 8.2 BMI categories and age

Output:

`results/bmi_age_comparison.png`

Generated by:

`scripts/plot_bmi_age_comparison.py`

This graph compares the descriptive Type 2 diabetes percentage across the four BMI categories and different age groups.

All available groups are displayed. An `x` marker identifies groups with fewer than 20 classified Type 2 diabetes cases.

The threshold of 20 cases is an exploratory display choice. It is not a formal statistical reliability standard.

## 9. Project Structure

The current project structure is organized as follows:

```text
enquete-maladie/
├── data/
│   ├── LLCP2022ASC.zip              # Original archive (not tracked)
│   └── LLCP2022.ASC                 # Extracted dataset (not tracked)
│
├── docs/
│   └── variable_layout.html         # CDC variable documentation
│
├── results/
│   ├── age_diabetes.csv
│   ├── bmi_diabetes_comparison.csv
│   ├── age_bmi_diabetes.csv
│   ├── age_bmi_diabetes_python.csv
│   ├── obesity_age.png
│   └── bmi_age_comparison.png
│
├── scripts/
│   ├── plot_obesity_age.py
│   └── plot_bmi_age_comparison.py
│
├── tests/
├── logs/
├── archive/
├── .gitignore
└── README.md
```

The Python reproduction CSV is retained separately to make the comparison with the AWK-generated result reproducible.

## 10. Requirements and Execution

### 10.1 Python requirements

The project uses Python and the following libraries:

- Pandas
- NumPy
- Matplotlib

Install the required packages using:

```bash
python -m pip install pandas numpy matplotlib
```

### 10.2 Running the visualization scripts

Run the following commands from the project root directory.

Generate the obesity-by-age graph:

```bash
python scripts/plot_obesity_age.py
```

Generate the age-and-BMI comparison graph:

```bash
python scripts/plot_bmi_age_comparison.py
```

Both scripts save their generated images inside the `results/` directory.

The CSV summaries were produced during the project's data-processing work. The visualization commands above regenerate the corresponding graphs from the data expected by each script.

## 11. Limitations and Responsible Interpretation

The results must be interpreted with the following limitations in mind:

- **Exploratory analysis:** The project focuses on descriptive statistics and visual comparisons.
- **Unweighted data:** The analyses do not apply BRFSS survey weights. The percentages are not official CDC weighted prevalence estimates.
- **Selected records:** Some analyses use a subset of state or territory codes. The selection criteria and coverage require validation against the official CDC documentation.
- **Restricted denominator:** The age-and-BMI percentage includes only respondents classified as Type 2 diabetes or no diabetes.
- **Excluded responses:** Other diabetes classifications, unknown diabetes types, refused answers, and missing values are not included in the main comparison.
- **Small groups:** Percentages based on small numbers of Type 2 diabetes cases may be unstable. The fewer-than-20 indicator is a descriptive warning, not a formal reliability measure.
- **No causal conclusions:** Observed relationships between age, BMI, and diabetes do not demonstrate that one variable causes another.
- **Population generalization:** The findings should not be generalized to the entire US population or to other populations without an appropriate analysis of the BRFSS sampling design, survey weights, and selection criteria.

## 12. Current Project Status

### Completed

- Downloaded and inspected the CDC BRFSS 2022 ASCII dataset.
- Examined the fixed-width record structure.
- Located the main variables using the CDC variable layout documentation.
- Explored diabetes response codes and missing values.
- Investigated state and territory coverage.
- Produced CSV summaries for age, BMI, and their combination.
- Checked the consistency of calculated percentages.
- Created two Python visualization scripts.
- Generated and saved two graphical visualizations.
- Reproduced the age-and-BMI analysis using Python and Pandas.
- Compared AWK and Python outputs and confirmed identical results.

### Remaining documentation and validation work

- Validate variable positions and response codes against the official CDC documentation.
- Confirm the exact reason for the selected state and territory subset.
- Document the exact selection criteria used by each analysis.
- Review the final repository contents and ensure that unnecessary or large raw data files are excluded.
- Complete the final interpretation and presentation of the results.

## 13. Data Source and References

Centers for Disease Control and Prevention (CDC).

**Behavioral Risk Factor Surveillance System (BRFSS), 2022 Annual Data.**

Official dataset:

https://www.cdc.gov/brfss/annual_data/2022/files/LLCP2022ASC.zip

CDC BRFSS official information:

https://www.cdc.gov/brfss/

The dataset and its official documentation are the primary sources for the variables and responses used in this project.

## 14. Reproducibility and Validation

The combined age, BMI, and diabetes analysis was independently reproduced using Python and Pandas.

The Python implementation processed the original fixed-width BRFSS 2022 dataset in chunks to reduce memory usage.

The resulting file, `results/age_bmi_diabetes_python.csv`, was compared with the original Bash/AWK output, `results/age_bmi_diabetes.csv`.

Validation results:

- Original AWK output: 52 rows.
- Python output: 52 rows.
- All columns and values were identical.

This confirms that the Python implementation reproduces the existing combined analysis results.

**Note:** The original Bash/AWK extraction commands were executed interactively and were not preserved as standalone scripts. The Python reproduction is available as a validation result, while the two saved Python scripts generate the visualizations.
