# Enquête sur une maladie — Type 2 Diabetes (BRFSS 2022)

Reproducible pipeline that downloads the CDC BRFSS 2022 survey, filters it, and measures the share of Type 2 diabetes by age group and BMI category.

## Project structure

```text
enquete-maladie/
├── run.sh                    # Main pipeline: runs everything
├── requirements.txt          # Python dependencies
├── README.md                 # Full documentation
├── README_V2.md              # This file
├── SOURCES.md                # Dataset source, URL and download date
├── LIEN_GIT.txt              # Repository URL and final commit hash
├── checksums/
│   └── LLCP2022ASC.zip.sha256    # Expected SHA-256 of the dataset
├── cron/
│   └── enquete-maladie.cron.example  # Scheduled run (cron)
├── data/                     # Downloaded dataset (created by run.sh, not in Git)
├── docs/
│   ├── rapport.pdf           # Project report
│   └── variable_layout.html  # CDC map of variable positions
├── gui/
│   ├── server.py             # Local web interface
│   └── static/index.html
├── scripts/
│   ├── reproduce_age_bmi_diabetes.py  # Analysis → results CSV
│   ├── plot_obesity_age.py            # Figure 1
│   └── plot_bmi_age_comparison.py     # Figure 2
├── tests/
│   └── test_analysis.py      # Automated tests
├── results/                  # CSV and figures
├── logs/                     # Timestamped run logs (created by run.sh)
└── archive/                  # Dated .tar.gz of results (created by run.sh)
```

## 1. Installation

### Prerequisites

| Tool | Notes |
| --- | --- |
| Bash | to run `run.sh` |
| Python **3.11 or newer** | required by pandas 3.x — https://www.python.org/downloads/ |
| `curl`, `unzip`, `tar`, `awk`, `tee`, `sha256sum` or `shasum` | standard command-line tools |
| Git | to clone the repository |

`run.sh` finds a suitable Python by itself (`python3`, `python3.12`, `python`…): it picks the first one that is 3.11 or newer and has the dependencies installed, and prints which one it uses. If none is found, it stops with a message saying what to install.

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/oussamapop/enquete-maladie.git
cd enquete-maladie

# 2. Install the Python dependencies (pandas, numpy, matplotlib)
python3 -m pip install -r requirements.txt
```

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
5. Runs the analysis and writes the results CSV
6. Generates the two figures
7. Runs the automated tests
8. Archives the results in a dated `.tar.gz`

Each run writes a timestamped log in `logs/`.

### Options

| Command | Description |
| --- | --- |
| `./run.sh -h` | Show the help |
| `./run.sh -f` | Force a new download of the dataset (use if the zip is corrupted or the checksum fails) |
| `./run.sh -s` | Skip the automated tests |
| `./run.sh -v` | Verbose: show each command as it runs; main steps are highlighted with `==>` |

Options can be combined, e.g. `./run.sh -v -s`.

### Interruption and rerun

- **Ctrl+C** stops the pipeline: temporary files are removed and the script exits with code `130`.
- The pipeline can be run again at any time without manual cleanup.
- On error, the script stops with a clear `ERROR:` message and a non-zero exit code.

### Run the tests alone

```bash
python3 -m unittest discover -s tests -v
```

### Graphical interface (optional)

```bash
python3 gui/server.py
```

Opens http://127.0.0.1:8765/ in the browser, to run the pipeline and view results, figures and logs.

### Scheduled run (cron)

The example in `cron/enquete-maladie.cron.example` runs the pipeline every day at 08:00:

1. Replace `/path/to/enquete-maladie` with the project path (`pwd` prints it)
2. `crontab -e` and paste the lines from the example file
3. `crontab -l` to check it is installed

Output goes to `logs/cron.log`.

## 3. Work distribution (répartition du travail)

**Shared by all members:** choice of the topic and dataset, documentation (`README.md`, `SOURCES.md`), report (`rapport.pdf`) and testing.

| Member | Contributions |
| --- | --- |
| Oussama Larbi | Data exploration (Bash/AWK); Python analysis and figures; automated tests; first `run.sh` pipeline; checksum |
| Massil | Cross-platform compatibility (Python auto-detection, checksum tool fallback, file name with trailing space); `trap` cleanup on interruption; read-only raw data; verbose mode (`-v`); runnable cron task; graphical interface (`gui/`) |
| _Member 3_ | _to complete_ |
| _Member 4_ | _to complete_ |
| _Member 5_ | _to complete_ |

## 4. Produced files (description des fichiers produits)

Files created by `./run.sh`:

| File | Description |
| --- | --- |
| `data/LLCP2022ASC.zip` | CDC dataset archive, downloaded and checksum-verified (read-only) |
| `data/LLCP2022.ASC` | Extracted fixed-width dataset, 445,132 records (read-only) |
| `results/age_bmi_diabetes_python.csv` | Main results: one row per age group × BMI category (52 rows) |
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
