# Enquête sur une maladie — Type 2 Diabetes Analysis

## 1. Project Overview

This project explores Type 2 diabetes using data from the 2022 Behavioral Risk Factor Surveillance System (BRFSS), published by the Centers for Disease Control and Prevention (CDC).

The main objective is to examine descriptive relationships between Type 2 diabetes, age groups, and Body Mass Index (BMI) categories.

The project combines Bash, AWK, Python, Pandas, NumPy, and Matplotlib to process a large fixed-width dataset, calculate descriptive statistics, generate visualizations, and validate analysis results.

The project follows a data-analysis workflow, from inspecting the original dataset to producing and validating summary files.

This is an exploratory descriptive study. It does not aim to establish causal relationships.

## 2. Research Objectives

The project aims to:

- Explore diabetes-related responses in the BRFSS 2022 dataset.
- Distinguish respondents classified as having Type 2 diabetes from respondents reporting no diabetes.
- Examine the distribution of these two groups across age categories.
- Compare BMI-category distributions between the two groups.
- Explore the relationship between age, BMI categories, and Type 2 diabetes.
- Produce CSV summaries and graphical visualizations.
- Reproduce an existing analysis using Python and Pandas.
- Validate the consistency of results obtained using different tools.

## 3. Dataset

The project uses the CDC BRFSS 2022 combined landline and cellular telephone ASCII dataset.

**Official dataset download:**

https://www.cdc.gov/brfss/annual_data/2022/files/LLCP2022ASC.zip

The downloaded archive is:

`data/LLCP2022ASC.zip`

The extracted dataset is:

`data/LLCP2022.ASC`

The dataset contains 445,132 respondent records. Each record uses a fixed-width format, with approximately 2,052 characters.

Unlike a CSV file, variables are stored at specific character positions rather than separated by commas.

The raw dataset is excluded from Git because of its large size. Anyone wishing to reproduce the analysis must download the official archive, extract it, and place `LLCP2022.ASC` inside the project's `data/` directory.

## 4. Tools and Technologies

- **Bash / Git Bash:** Command-line navigation, file management, and data exploration.
- **AWK:** Processing fixed-width records and calculating descriptive summaries.
- **Python:** Data processing, validation, and visualization.
- **Pandas:** Reading, filtering, grouping, and comparing datasets.
- **NumPy:** Numerical computing.
- **Matplotlib:** Generating graphical visualizations.
- **Git and GitHub:** Version control and project management.

## 5. Data Preparation and Variables

### 5.1 Fixed-width data format

The BRFSS ASCII dataset uses fixed-width records.

The variable positions were identified using the CDC variable layout documentation:

`docs/variable_layout.html`

The main variables used are:

| Variable   | Description                   |
| ---------- | ----------------------------- |
| `DIABETE4` | Diabetes status               |
| `DIABTYPE` | Diabetes type                 |
| `_AGEG5YR` | Age group                     |
| `_BMI5`    | Calculated BMI value          |
| `_BMI5CAT` | BMI category                  |
| `_RFBMI5`  | BMI-related derived indicator |

The Python implementation extracts the following fields using zero-based character intervals:

| Field      | Character interval |
| ---------- | ------------------ |
| State code | `(0, 2)`           |
| `DIABETE4` | `(128, 129)`       |
| `DIABTYPE` | `(270, 271)`       |
| `_AGEG5YR` | `(1980, 1982)`     |
| `_BMI5CAT` | `(2001, 2002)`     |

The starting position is included and the ending position is excluded, following Python's slicing convention.

### 5.2 Diabetes classification

The main comparison uses two groups:

- **Type 2 diabetes:** `DIABETE4 = 1` and `DIABTYPE = 2`.
- **No diabetes:** `DIABETE4 = 3`.

Other responses, including other diabetes classifications, unknown responses, refused responses, and missing values, are excluded from this two-group comparison.

The classification is based on the response codes in the BRFSS dataset.

### 5.3 Age and BMI categories

For the age analysis:

- Age codes `01` to `13` are retained.
- Age code `14` and other values are excluded.

For the BMI analysis, the following `_BMI5CAT` codes are retained:

| Code | BMI category  |
| ---- | ------------- |
| 1    | Underweight   |
| 2    | Normal weight |
| 3    | Overweight    |
| 4    | Obese         |

Only records satisfying the relevant selection and classification criteria are included in each analysis.

### 5.4 Selected states and territories

The analysis is restricted to 13 reporting areas:

| State or territory  | BRFSS code |
| ------------------- | ---------- |
| Delaware            | 10         |
| Georgia             | 13         |
| Indiana             | 18         |
| Maine               | 23         |
| Mississippi         | 28         |
| Missouri            | 29         |
| Nevada              | 32         |
| North Dakota        | 38         |
| South Carolina      | 45         |
| South Dakota        | 46         |
| Vermont             | 50         |
| Wisconsin           | 55         |
| U.S. Virgin Islands | 78         |

These reporting areas were selected because the 2022 BRFSS Diabetes optional module was administered in these areas.

The diabetes-type question (`DIABTYPE`) was needed to distinguish Type 2 diabetes from other diabetes categories. Therefore, the analysis was restricted to the reporting areas where the relevant Diabetes module data were available.

CDC documentation:

https://www.cdc.gov/brfss/questionnaires/modules/category2022.htm

The selected areas account for 92,432 records in the dataset.

The findings describe the selected reporting areas and should not be generalized to all US states or the entire US population.

## 6. Analysis Workflow

### 6.1 Bash and AWK data exploration

Bash and AWK were used to explore and process the original ASCII dataset.

The work included:

- Inspecting the dataset's record length and number of records.
- Examining diabetes response codes.
- Investigating the availability of diabetes-type responses.
- Identifying the relevant state and territory codes.
- Counting respondents by age group and BMI category.
- Calculating descriptive percentages.
- Identifying groups with fewer than 20 classified Type 2 diabetes cases.

The original Bash/AWK extraction commands were executed interactively and were not preserved as standalone scripts.

### 6.2 Age and diabetes analysis

Output:

`results/age_diabetes.csv`

This file summarizes the number of respondents classified as having Type 2 diabetes and respondents reporting no diabetes across age groups.

It provides a descriptive comparison of the two groups by age.

### 6.3 BMI and diabetes analysis

Output:

`results/bmi_diabetes_comparison.csv`

This file compares the distribution of BMI categories between the Type 2 diabetes and no-diabetes groups.

It contains the group, BMI category, count, percentage, and total number of valid BMI records used for the corresponding group.

### 6.4 Age, BMI, and diabetes analysis

Output:

`results/age_bmi_diabetes.csv`

This file combines age groups and BMI categories.

Each row represents one age-and-BMI combination and contains:

- `age_code`: Age-group code.
- `bmi_category`: BMI category.
- `type2_count`: Number of classified Type 2 diabetes cases.
- `no_diabetes_count`: Number of respondents reporting no diabetes.
- `total`: Total number of records in the two groups.
- `percentage`: Descriptive Type 2 diabetes percentage.
- `small_case_count`: Indicates whether the Type 2 diabetes count is below 20.

The percentage is calculated as:

`Type 2 cases / (Type 2 cases + No-diabetes cases) × 100`

This percentage describes the proportion of Type 2 diabetes cases among the two included groups within each age-and-BMI combination. It is not an estimate of diabetes prevalence in the entire population.

### 6.5 Python reproduction and validation

The age-and-BMI analysis was reproduced using Python and Pandas.

The script:

`scripts/reproduce_age_bmi_diabetes.py`

reads the original fixed-width dataset in chunks of 50,000 records to reduce memory usage.

The Python-generated output is:

`results/age_bmi_diabetes_python.csv`

This file was compared with the original AWK-generated output:

`results/age_bmi_diabetes.csv`

Both files contain 52 age-and-BMI groups and have identical values across all seven columns.

This confirms that the Python implementation reproduces the existing AWK results. It does not independently validate the scientific classification rules or the survey methodology.

## 7. Results Summary

The Python analysis produced the following results using the project's selection criteria:

| Description                                          |   Count |
| ---------------------------------------------------- | ------: |
| Total dataset records                                | 445,132 |
| Records in selected reporting areas                  |  92,432 |
| Valid records included in the age-and-BMI comparison |  76,519 |
| Classified Type 2 diabetes cases                     |   9,393 |
| Respondents reporting no diabetes                    |  67,126 |
| Age-and-BMI groups                                   |      52 |

These figures describe the records retained by the project's filters. They are not official CDC population prevalence estimates.

## 8. Visualizations

Python, Pandas, and Matplotlib are used to generate two graphical visualizations.

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

This graph compares the descriptive Type 2 diabetes percentage across four BMI categories and different age groups.

All available groups are displayed. An `x` marker identifies groups with fewer than 20 classified Type 2 diabetes cases.

The threshold of 20 cases is an exploratory display choice, not a formal statistical reliability standard.

## 9. Project Structure

The project is organized as follows:

```text
enquete-maladie/
├── data/
├── checksums/
├── docs/
├── results/
├── scripts/
├── tests/
├── logs/
├── archive/
├── cron/
├── gui/
├── run.sh
├── requirements.txt
├── SOURCES.md
├── .gitignore
└── README.md
```

- `data/`: CDC dataset files (excluded from Git).
- `checksums/`: Dataset integrity verification.
- `cron/`: Example cron job to run the pipeline automatically.
- `gui/`: Local graphical interface (see section 10).
- `docs/`: CDC variable documentation.
- `results/`: Generated CSV files and figures.
- `scripts/`: Python analysis and visualization scripts.
- `tests/`: Automated tests.
- `logs/`: Timestamped execution logs.
- `archive/`: Compressed results archives.

## 10. Installation and Execution

### 10.1 Prerequisites

The project requires the following tools:

- Python 3.11 or newer (pandas 3.x requires it; on macOS the built-in `python3` is 3.9, install a newer one e.g. `brew install python@3.12`)
- Bash
- Git
- `curl`
- `unzip`
- `sha256sum`
- `tar`
- `awk`
- `tee`

Python dependencies are listed in `requirements.txt`.

### 10.2 Clone the Repository

Clone the project repository:

```bash
git clone https://github.com/oussamapop/enquete-maladie.git
cd enquete-maladie
```

### 10.3 Install Python Dependencies

Install the required Python packages:

```bash
python3 -m pip install -r requirements.txt
```

The main dependencies include:

- Pandas: data manipulation and analysis.
- NumPy: numerical operations.
- Matplotlib: data visualization.

### 10.4 Dataset Preparation

The raw CDC BRFSS 2022 dataset is not included in the Git repository because of its large size.

The pipeline automatically downloads and prepares the dataset when it is not available locally.

The dataset integrity is checked using the SHA-256 checksum stored in the `checksums/` directory.

The raw dataset files are stored in the `data/` directory and excluded from Git using `.gitignore`.

### 10.5 Run the Complete Pipeline

Make the pipeline executable if necessary:

```bash
chmod +x run.sh
```

Run the complete analysis:

```bash
./run.sh
```

The pipeline automatically performs the following operations:

1. Checks the required commands and Python dependencies.
2. Verifies the dataset checksum.
3. Downloads and extracts the dataset if necessary.
4. Processes the BRFSS 2022 data.
5. Generates the analysis CSV file.
6. Creates the visualization images.
7. Displays summary information.
8. Executes automated tests.
9. Archives the generated results.

### 10.6 Available Options

The main script supports the following options:

| Command       | Description                        |
| ------------- | ---------------------------------- |
| `./run.sh -f` | Forces the dataset download again. |
| `./run.sh -s` | Skips automated tests.             |
| `./run.sh -v` | Verbose: shows each command as it runs, with its line number. |

**Interruption:** if the pipeline is stopped (Ctrl+C or `kill`), a `trap` removes the temporary download file (`data/LLCP2022ASC.zip.tmp`) and the script exits with code `130`. It can be run again without manual cleanup.

For example, to execute the pipeline without running tests:

```bash
./run.sh -s
```

### 10.7 Run Individual Analysis Scripts

The Python analysis can also be executed independently:

```bash
python3 scripts/reproduce_age_bmi_diabetes.py \
    --input data/LLCP2022.ASC \
    --output results/age_bmi_diabetes_python.csv \
    --chunk-size 50000
```

The script supports the following arguments:

- `--input`: path to the raw dataset.
- `--output`: path to the generated CSV file.
- `--chunk-size`: number of records processed per chunk.

### 10.8 Run Automated Tests

Execute the automated tests using:

```bash
python3 -m unittest discover -s tests -v
```

The tests validate the analysis calculations, categories, totals, percentages, and consistency between the Shell and Python implementations.

### 10.9 Generated Outputs

The pipeline generates the following files:

| File                                     | Description                                       |
| ---------------------------------------- | ------------------------------------------------- |
| `results/age_bmi_diabetes_python.csv`    | Age and BMI analysis results generated by Python. |
| `results/obesity_age.png`                | Visualization of obesity and age.                 |
| `results/bmi_age_comparison.png`         | Comparison of BMI categories across age groups.   |
| `logs/run_YYYYMMDD_HHMMSS.log`           | Timestamped execution log.                        |
| `archive/results_YYYYMMDD_HHMMSS.tar.gz` | Compressed archive of analysis results.           |

### 10.10 Automatic Execution with Cron

An example cron configuration is provided in:

`cron/enquete-maladie.cron.example`

On Linux, macOS or WSL, the pipeline can be scheduled to run automatically.

1. Replace `/path/to/enquete-maladie` with the absolute path to the project directory (`pwd` inside the project prints it).
2. Open the crontab editor:

```bash
crontab -e
```

3. Add the following lines:

```cron
PATH=/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin
0 8 * * * cd /path/to/enquete-maladie && mkdir -p logs && /bin/bash ./run.sh >> logs/cron.log 2>&1
```

4. Check that the job is installed:

```bash
crontab -l
```

This configuration runs the pipeline every day at 08:00. Standard output and errors are appended to `logs/cron.log`, and each run also writes its own `logs/run_YYYYMMDD_HHMMSS.log`.

**Why the `PATH` line:** cron starts jobs with a minimal `PATH`, so `python3`, `curl` or `sha256sum` may not be found and the job would fail silently. Add the directory where your Python 3.11+ is installed if it is not listed (e.g. `/opt/homebrew/bin` on macOS with Homebrew; `which python3` shows it).

**Note:** Git Bash on Windows does not provide a cron service by itself; use WSL.

### Graphical interface (GUI)

The project includes a graphical interface that runs in your web browser. It lets you run the pipeline and explore the results without typing commands. It only needs Python 3; no extra packages are required to start it.

#### How to launch the GUI

1. Open a terminal and go to the project folder:

   ```bash
   cd path/to/enquete-maladie
   ```

2. Start the GUI server:

   ```bash
   python3 gui/server.py
   ```

3. Your browser opens automatically at **http://127.0.0.1:8765/**. If it does not, copy this address into your browser.

4. **Keep the terminal open** while you use the interface. Closing the terminal or pressing `Ctrl+C` stops the website.

The server only listens on your own computer (`127.0.0.1`); it is not reachable from other machines.

#### Options

| Command | Description |
| --- | --- |
| `python3 gui/server.py` | Start on port 8765 and open the browser. |
| `python3 gui/server.py --port 8766` | Use another port. |
| `python3 gui/server.py --no-browser` | Start without opening the browser. |

#### Using the interface

| Tab | What it does |
| --- | --- |
| **Run pipeline** | Runs `./run.sh`. Tick **Force dataset download** (`-f`) or **Skip automated tests** (`-s`), then press **Run**. The log appears live with step progress. **Stop** interrupts the run like `Ctrl+C`, so temporary files are cleaned up. |
| **Overview** | Key figures, Type 2 prevalence by age group, BMI distribution comparison, and an age × BMI heatmap (hatched cells have fewer than 20 cases). |
| **Data tables** | Sortable, filterable views of each CSV file in `results/`, with download links. |
| **Figures** | The PNG graphs in `results/`. |
| **Logs & archives** | Previous run logs, `.tar.gz` result archives, and the final report. |

A **☾ Dark / ☀ Light** button in the top-right corner switches the theme.

On the first run, the dataset (about 50 MB compressed, 880 MB extracted) is downloaded and verified, which can take a few minutes. Charts, tables and figures refresh automatically when a run finishes.

#### Which Python runs the pipeline

The GUI automatically looks for a Python that has `pandas`, `numpy` and `matplotlib` installed (for example a Homebrew `python3.12`) and uses it to run `./run.sh`, even if the default `python3` does not have them. The first line of the log shows which one is used:

```text
[GUI] Using Python: /opt/homebrew/bin/python3.12
```

If none is found, install the dependencies first:

```bash
python3 -m pip install -r requirements.txt
```

#### Troubleshooting

| Problem | Solution |
| --- | --- |
| The page does not load | The server is not running. Start it again with `python3 gui/server.py` and keep the terminal open. |
| `Address already in use` | The GUI is already running: just open http://127.0.0.1:8765/. Or start it on another port with `--port 8766`. |
| `No module named 'pandas'` in the log | No Python with the dependencies was found. Run `python3 -m pip install -r requirements.txt`. |
| Overview shows "not found" | No results yet. Go to **Run pipeline** and press **Run**. |

## 11. Limitations and Responsible Interpretation

The findings must be interpreted with the following limitations:

- **Exploratory analysis:** The project focuses on descriptive statistics and visual comparisons.
- **Unweighted analysis:** The calculations do not apply BRFSS survey weights. The percentages are not official CDC weighted prevalence estimates.
- **Restricted geographic coverage:** The analysis uses 13 reporting areas where the Diabetes optional module was available. It does not represent all US states and territories.
- **Restricted denominator:** The age-and-BMI percentage includes only respondents classified as having Type 2 diabetes or no diabetes.
- **Excluded responses:** Other diabetes classifications, unknown diabetes types, refused answers, and missing or invalid age and BMI values are excluded from the relevant comparisons.
- **Small groups:** Percentages based on small numbers of Type 2 diabetes cases may be unstable. The fewer-than-20 indicator is a descriptive warning, not a formal statistical reliability measure.
- **No causal conclusions:** Observed relationships between age, BMI, and diabetes do not demonstrate that one variable causes another.
- **Population generalization:** The results should not be generalized to the entire US population without an appropriate analysis of the BRFSS sampling design, survey weights, and geographic coverage.

## 12. Project Status

### Completed

- Downloaded and inspected the CDC BRFSS 2022 ASCII dataset.
- Examined the fixed-width record structure.
- Located the main variables using CDC documentation.
- Explored diabetes response codes and data availability.
- Identified the 13 reporting areas using the Diabetes module.
- Produced age, BMI, and combined age-and-BMI CSV summaries.
- Created two Python visualization scripts.
- Generated and saved two graphical visualizations.
- Reproduced the age-and-BMI analysis using Python and Pandas.
- Confirmed that the AWK and Python outputs are identical.
- Added Python dependencies in `requirements.txt`.
- Created nine automated tests and confirmed that all nine pass.
- Documented the methodology and statistical limitations.

### Final repository tasks

- Review the final Git status.
- Commit and push the latest project files.
- Merge the `analysis-improvements` branch into `main`.
- Verify that the final GitHub repository contains the expected files.

## 13. Data Sources and References

**Centers for Disease Control and Prevention (CDC).**

Behavioral Risk Factor Surveillance System (BRFSS), 2022 Annual Data.

Official dataset:

https://www.cdc.gov/brfss/annual_data/2022/files/LLCP2022ASC.zip

2022 BRFSS data and documentation:

https://www.cdc.gov/brfss/annual_data/annual_2022.html

2022 BRFSS modules by category:

https://www.cdc.gov/brfss/questionnaires/modules/category2022.htm

2022 BRFSS questionnaires:

https://www.cdc.gov/brfss/questionnaires/

The CDC dataset, codebook, questionnaire, and variable-layout documentation are the primary sources for the variables and responses used in this project.

## 14. Reproducibility and Validation

The combined age, BMI, and diabetes analysis was reproduced using Python and Pandas.

The Python implementation processed the original fixed-width dataset in chunks to reduce memory usage.

The resulting file, `results/age_bmi_diabetes_python.csv`, was compared with the original Bash/AWK output, `results/age_bmi_diabetes.csv`.

Validation results:

- Original AWK output: 52 rows.
- Python output: 52 rows.
- All seven columns and their values were identical.
- All nine automated tests passed.

This confirms consistency between the two implementations for the current analysis criteria.

It does not independently validate the scientific assumptions, survey weighting, or statistical representativeness of the results.

**Note:** The original Bash/AWK extraction commands were executed interactively and were not preserved as standalone scripts. The Python reproduction script is available for reproducing the combined age-and-BMI analysis from the original dataset.

## 15. Work Distribution and Contributions

At the current stage of the project, the work has been carried out entirely by one contributor oussama larbi .

The following tasks were completed independently:

- Research topic selection and project planning.
- CDC BRFSS 2022 dataset acquisition and preparation.
- Data cleaning, processing, and analysis.
- Development of Python analysis and visualization scripts.
- Development of the Shell automation pipeline (`run.sh`).
- Implementation of automated tests.
- Dataset integrity verification using SHA-256 checksums.
- Project documentation (`README.md` and `SOURCES.md`).
- Pipeline testing and reproducibility verification.

The current contribution distribution reflects the work completed so far. It may be revised after discussion with the other group members to reflect any additional contributions or changes in responsibilities.
