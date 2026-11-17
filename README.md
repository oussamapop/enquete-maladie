# Enquête sur une maladie — Type 2 Diabetes (BRFSS 2022)

Reproducible pipeline that downloads the CDC BRFSS 2022 survey, filters it with shell tools and Python, and measures the share of Type 2 diabetes by age group and BMI category, with confidence intervals and chi-square tests.

## Project structure

```text
enquete-maladie/
├── run.sh                    # Main pipeline: runs everything
├── requirements.txt          # Python dependencies (exact versions)
├── .gitattributes            # Keeps LF line endings for shell scripts
├── README.md                 # This file
├── SOURCES.md                # Dataset source, URL and download date
├── LIEN_GIT.txt              # Repository URL and final commit hash
├── checksums/
│   └── LLCP2022ASC.zip.sha256    # Expected SHA-256 of the dataset
├── cron/
│   └── enquete-maladie.cron.example  # Scheduled run (cron)
├── data/                     # Downloaded dataset (created by run.sh, not in Git)
├── docs/
│   ├── rapport.pdf           # Project report (4 pages)
│   └── variable_layout.html  # CDC map of variable positions
├── gui/
│   ├── server.py             # Local web interface
│   └── static/index.html
├── scripts/
│   ├── shell_filter.sh                # Shell filtering of the raw data (cut | grep | awk | sort | uniq)
│   ├── reproduce_age_bmi_diabetes.py  # Analysis → results CSV
│   ├── stats_analysis.py              # Confidence intervals, chi-square tests → stats.json
│   ├── plot_obesity_age.py            # Figure 1
│   └── plot_bmi_age_comparison.py     # Figure 2
├── tests/
│   ├── test_analysis.py      # Tests on the results files (incl. shell vs Python)
│   └── test_processing.py    # Tests of the processing on a synthetic sample
├── results/                  # CSV, JSON and figures
├── logs/                     # Timestamped run logs (created by run.sh)
├── archive/                  # Dated .tar.gz of results (created by run.sh)
└── .venv/                    # Python virtual environment (created at installation, not in Git)
```

## 1. Installation

### Prerequisites

| Tool | Notes |
| --- | --- |
| Bash | to run `run.sh` |
| Python **3.11 or newer** | required by pandas 3.x — https://www.python.org/downloads/ |
| `curl`, `unzip`, `tar`, `cut`, `grep`, `awk`, `sort`, `uniq`, `tee`, `sha256sum` or `shasum` | standard command-line tools |
| Git | to clone the repository |

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/oussamapop/enquete-maladie.git
cd enquete-maladie

# 2. Create an isolated Python environment in .venv
python3 -m venv .venv

# 3. Install the exact dependency versions (pandas, numpy, matplotlib) into it
.venv/bin/python -m pip install -r requirements.txt
```

On Windows (Git Bash), step 3 is `.venv/Scripts/python.exe -m pip install -r requirements.txt`.

There is no need to activate the environment: `run.sh` uses `.venv` automatically when it exists and prints which Python it uses. Without `.venv`, it looks for a system Python 3.11+ that has the dependencies, and stops with a clear message if there is none.

The dataset is **not** in the repository: `run.sh` downloads it automatically on the first run.

## 2. Usage (mode d'emploi)

### Run the full pipeline

```bash
./run.sh
```

It runs these steps automatically:

1. Checks the required commands and Python packages
2. Downloads the CDC dataset (about 50 MB), unless it is already there
3. Verifies its SHA-256 checksum and extracts it (about 914 MB)
4. Sets the raw data to read-only
5. Filters the raw data with a shell pipe (`cut | grep | awk | sort | uniq -c`) and writes three CSV summaries
6. Runs the Python analysis and writes the results CSV
7. Computes the statistics (95% confidence intervals, chi-square tests) → `stats.json`
8. Generates the two figures
9. Runs the 18 automated tests
10. Archives the results in a dated `.tar.gz`

Each run writes a timestamped log in `logs/`. A full run takes about 2 minutes once the data is downloaded.

### Options

| Command | Description |
| --- | --- |
| `./run.sh -h` | Show the help |
| `./run.sh -f` | Force a new download of the dataset (use if the zip is corrupted or the checksum fails) |
| `./run.sh -s` | Skip the automated tests |
| `./run.sh -v` | Verbose: show each command as it runs; main steps are highlighted with `==>` |

Options can be combined, e.g. `./run.sh -v -s`.

### Interruption, errors and rerun

- **Ctrl+C** stops the pipeline: temporary files are removed and the script exits with code `130`.
- The pipeline can be run again at any time without manual cleanup.
- On error, the script stops at the first failing command with a clear `ERROR:` message (the failed step, or the line number and command) and a non-zero exit code.

| Exit code | Meaning |
| --- | --- |
| `0` | Pipeline completed |
| `1` | Error (missing file, wrong checksum, failed step…) |
| `130` | Interrupted (Ctrl+C) |

### Run the tests alone

```bash
.venv/bin/python -m unittest discover -s tests -v
```

`test_processing.py` builds a small synthetic file with known results, so it does not need the dataset. `test_analysis.py` checks the results files.

### Graphical interface (optional)

```bash
.venv/bin/python gui/server.py
```

Opens http://127.0.0.1:8765/ in the browser, to run the pipeline and view results, figures and logs.

### Scheduled run (cron)

The example in `cron/enquete-maladie.cron.example` runs the pipeline every day at 08:00:

1. Replace `/path/to/enquete-maladie` with the project path (`pwd` prints it)
2. `crontab -e` and paste the lines from the example file
3. `crontab -l` to check it is installed

Output goes to `logs/cron.log`. The scheduled run uses `.venv` like a manual run.

## 3. Work distribution (répartition du travail)

**Shared by all members:** choice of the topic and dataset, documentation (`README.md`, `SOURCES.md`), report (`rapport.pdf`) and testing.

| Member | Contributions |
| --- | --- |
| Oussama Larbi | Data exploration (Bash/AWK); Python analysis and figures; automated tests; first `run.sh` pipeline; checksum |
| Massil | Cross-platform compatibility (Python auto-detection, checksum tool fallback, file name with trailing space); `trap` cleanup on interruption; read-only raw data; verbose mode (`-v`); runnable cron task; graphical interface (`gui/`) |
| Rahabi Abdelmalek | Shell filtering of the raw data (`scripts/shell_filter.sh`, pipe `cut`, `grep`, `awk`, `sort`, `uniq -c`) regenerating the three reference CSVs; `ERR` trap and step failure messages in `run.sh`; executable scripts and shebangs; LF line endings (`.gitattributes`); repository cleanup |
| Zahaf Moussaab Abdel Settar | Isolated environment (`.venv`, exact versions in `requirements.txt`, `.venv` detection in `run.sh`); statistical analysis (`scripts/stats_analysis.py`: Wilson 95% intervals, chi-square tests, obese/normal ratio → `stats.json`); processing split into testable functions; tests on a synthetic sample (`tests/test_processing.py`) |
| _Member 5_ | _to complete_ |

## 4. Produced files (description des fichiers produits)

Files created by `./run.sh`:

| File | Description |
| --- | --- |
| `data/LLCP2022ASC.zip` | CDC dataset archive, downloaded and checksum-verified (read-only) |
| `data/LLCP2022.ASC` | Extracted fixed-width dataset, 445,132 records (read-only) |
| `results/age_bmi_diabetes.csv` | Shell result: Type 2 % by age group × BMI category (must equal the Python result, checked by the tests) |
| `results/age_diabetes.csv` | Shell result: Type 2 vs no diabetes by age group |
| `results/bmi_diabetes_comparison.csv` | Shell result: BMI distribution of the Type 2 and no-diabetes groups |
| `results/age_bmi_diabetes_python.csv` | Main results: one row per age group × BMI category (52 rows) |
| `results/stats.json` | Statistics: confidence intervals, chi-square tests, obese/normal ratio (see below) |
| `results/obesity_age.png` | Figure: Type 2 diabetes percentage by age group, obese respondents only |
| `results/bmi_age_comparison.png` | Figure: Type 2 diabetes percentage by age group, for the 4 BMI categories |
| `logs/run_YYYYMMDD_HHMMSS.log` | Timestamped log of each run |
| `archive/results_YYYYMMDD_HHMMSS.tar.gz` | Dated archive of the `results/` folder |
| `logs/cron.log` | Output of scheduled runs (only when cron is used) |

### Columns of `age_bmi_diabetes_python.csv`

| Column | Meaning |
| --- | --- |
| `age_code` | Age group, `01` (18–24) to `13` (80+) |
| `bmi_category` | `1` underweight, `2` normal, `3` overweight, `4` obese |
| `type2_count` | Respondents with Type 2 diabetes |
| `no_diabetes_count` | Respondents without diabetes |
| `total` | `type2_count + no_diabetes_count` |
| `percentage` | `type2_count / total × 100` |
| `small_case_count` | `YES` if fewer than 20 Type 2 cases (less reliable) |

### Content of `stats.json`

| Key | Meaning |
| --- | --- |
| `overall` | Type 2 count, total, percentage and 95% Wilson interval (`ci_low`, `ci_high`) |
| `chi_square` | For BMI and for age: statistic, degrees of freedom, p-value, significant at 5% or not |
| `obese_vs_normal_by_age` | Type 2 % of obese and normal-BMI respondents and their `ratio`; `reliable` is false when one of them has fewer than 20 cases |
| `groups` | The 52 age × BMI groups with their percentage and 95% interval |
