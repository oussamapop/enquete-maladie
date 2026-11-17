#!/usr/bin/env bash

# Stop at the first failing command (-e), also inside functions (-E),
# on unset variables (-u) and on a failure anywhere in a pipe (pipefail)
set -Eeuo pipefail

# --------------------------------------------------
# 1. Project configuration
# --------------------------------------------------

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

DATA_DIR="$PROJECT_DIR/data"
RESULTS_DIR="$PROJECT_DIR/results"
LOG_DIR="$PROJECT_DIR/logs"
ARCHIVE_DIR="$PROJECT_DIR/archive"

ZIP_FILE="$DATA_DIR/LLCP2022ASC.zip"
TEMP_FILE="$ZIP_FILE.tmp"
ASC_FILE="$DATA_DIR/LLCP2022.ASC"
CHECKSUM_FILE="$PROJECT_DIR/checksums/LLCP2022ASC.zip.sha256"

DATA_URL="https://www.cdc.gov/brfss/annual_data/2022/files/LLCP2022ASC.zip"

FORCE_DOWNLOAD=false
SKIP_TESTS=false
VERBOSE=false
PYTHON=""
USE_COLOR=false

# --------------------------------------------------
# 2. Functions
# --------------------------------------------------

log() {
    # Hide the internals of log itself from the verbose trace
    { [[ $- == *x* ]] && local trace=on || local trace=off; set +x; } 2>/dev/null

    local message="[$(date '+%Y-%m-%d %H:%M:%S')] $*"

    if [[ "$VERBOSE" == true ]]; then
        # Highlight main steps: "==>" marker, bold green on a terminal
        if [[ "$USE_COLOR" == true ]]; then
            printf '\033[1;32m==> %s\033[0m\n' "$message"
        else
            printf '==> %s\n' "$message"
        fi
    else
        echo "$message"
    fi

    if [[ "$trace" == on ]]; then set -x; fi
}

die() {
    log "ERROR: $*"
    exit 1
}

require_command() {
    command -v "$1" >/dev/null 2>&1 || die "Required command not found: $1"
}

# Find a Python 3.11+ that has the dependencies.
# The project virtual environment (.venv, see README) is tried first;
# otherwise the command name differs between systems (python3, python3.12, python...).
find_python() {
    local candidate first_ok=""

    for candidate in \
        "$PROJECT_DIR/.venv/bin/python" \
        "$PROJECT_DIR/.venv/Scripts/python.exe" \
        python3 python3.14 python3.13 python3.12 python3.11 python; do
        command -v "$candidate" >/dev/null 2>&1 || continue

        # Skip versions older than 3.11
        "$candidate" -c 'import sys; sys.exit(sys.version_info < (3, 11))' 2>/dev/null || continue

        if [[ -z "$first_ok" ]]; then first_ok="$candidate"; fi

        if "$candidate" -c 'import pandas, numpy, matplotlib' 2>/dev/null; then
            PYTHON="$candidate"
            return 0
        fi
    done

    if [[ -n "$first_ok" ]]; then
        die "Python dependencies are missing. Create the environment described in README.md (python3 -m venv .venv, then pip install -r requirements.txt)."
    fi

    die "Python 3.11 or newer is required but was not found. Install it from https://www.python.org/downloads/"
}

# Print the SHA-256 of a file (sha256sum on Linux, shasum on other systems)
sha256_of() {
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$1"
    else
        shasum -a 256 "$1"
    fi | awk '{print $1}'
}

# Remove temporary files (called on every exit)
cleanup() {
    rm -f "$TEMP_FILE"
}

# Called on Ctrl+C (INT) or kill (TERM)
on_interrupt() {
    log "Interrupted. Removing temporary files..."
    cleanup
    exit 130
}

# Called on any failing command (ERR): clear message, then stop with its exit code
on_error() {
    local status="$1"
    local line="$2"
    local command="$3"

    log "ERROR: command failed with exit code $status at line $line: $command"
    exit "$status"
}

trap on_interrupt INT TERM
trap cleanup EXIT
trap 'on_error $? $LINENO "$BASH_COMMAND"' ERR

show_help() {
    cat <<HELP
Usage: ./run.sh [OPTIONS]

Runs the whole pipeline: download and check the BRFSS 2022 data,
shell filtering, Python analysis, statistics, figures, tests, archive.

Options:
  -h    Show this help
  -f    Force dataset download
  -s    Skip automated tests
  -v    Verbose: show each command as it runs

Exit codes: 0 success, 1 error, 130 interrupted (Ctrl+C)
HELP
}

verify_checksum() {
    local file="$1"
    local expected actual

    expected="$(awk '{print $1}' "$CHECKSUM_FILE")"
    actual="$(sha256_of "$file")"

    if [[ "$actual" != "$expected" ]]; then
        return 1
    fi

    return 0
}

download_dataset() {
    log "Downloading BRFSS 2022 dataset..."

    rm -f "$TEMP_FILE"

    curl -fL --retry 3 \
        --output "$TEMP_FILE" \
        "$DATA_URL" || die "Dataset download failed."

    log "Verifying downloaded dataset checksum..."

    if ! verify_checksum "$TEMP_FILE"; then
        die "Checksum verification failed. Downloaded file does not match the expected SHA256."
    fi

    unzip -tq "$TEMP_FILE" || die "Downloaded ZIP archive is invalid."

    mv "$TEMP_FILE" "$ZIP_FILE"

    log "Dataset downloaded and verified successfully."
}

prepare_dataset() {

    # Raw data is read-only (444): unlock it so it can be replaced or re-extracted
    chmod u+w "$ZIP_FILE" "$ASC_FILE" 2>/dev/null || true

    if [[ "$FORCE_DOWNLOAD" == true ]]; then
        download_dataset

    elif [[ -f "$ZIP_FILE" ]]; then

        log "Dataset archive already exists. Checking checksum..."

        verify_checksum "$ZIP_FILE" \
            || die "Existing ZIP checksum is incorrect. Run ./run.sh -f to download it again."

        unzip -tq "$ZIP_FILE" \
            || die "Existing ZIP archive is damaged."

    else
        download_dataset
    fi

    if [[ ! -f "$ASC_FILE" || "$FORCE_DOWNLOAD" == true ]]; then

        log "Extracting dataset..."

        unzip -oq "$ZIP_FILE" -d "$DATA_DIR" \
            || die "Dataset extraction failed."

        # The CDC archive stores the file as "LLCP2022.ASC " (trailing space)
        if [[ -f "$ASC_FILE " ]]; then
            mv -f "$ASC_FILE " "$ASC_FILE"
        fi

    else
        log "Extracted dataset already exists."
    fi

    [[ -s "$ASC_FILE" ]] \
        || die "Dataset file is missing or empty: $ASC_FILE"

    # Protect the raw data: read-only for everyone
    chmod 444 "$ZIP_FILE" "$ASC_FILE"

    log "Dataset is ready (raw data set to read-only)."
}

run_step() {
    local description="$1"
    shift

    log "$description"
    "$@" || die "Step failed: $description"
    log "Completed: $description"
}

# --------------------------------------------------
# 3. Read command-line options
# --------------------------------------------------

while getopts ":hfsv" option; do
    case "$option" in
        h)
            show_help
            exit 0
            ;;
        f)
            FORCE_DOWNLOAD=true
            ;;
        s)
            SKIP_TESTS=true
            ;;
        v)
            VERBOSE=true
            ;;
        :)
            echo "Option -$OPTARG requires an argument."
            show_help
            exit 1
            ;;
        \?)
            echo "Unknown option: -$OPTARG"
            show_help
            exit 1
            ;;
    esac
done

# --------------------------------------------------
# 4. Create project directories and log
# --------------------------------------------------

mkdir -p "$DATA_DIR" "$RESULTS_DIR" "$LOG_DIR" "$ARCHIVE_DIR"

LOG_FILE="$LOG_DIR/run_$(date '+%Y%m%d_%H%M%S').log"

# Colors only when the output is a terminal (checked before redirecting)
if [[ -t 1 ]]; then USE_COLOR=true; fi

# tee ignores Ctrl+C so the interruption message still reaches the log;
# awk removes color codes (log file stays plain text) and writes each line
# immediately (fflush) so nothing is lost if the script is interrupted
exec > >(trap '' INT; tee >(awk '{ gsub(/\033\[[0-9;]*m/, ""); print; fflush() }' >> "$LOG_FILE")) 2>&1

log "========================================"
log "Starting Enquête sur une maladie"
log "========================================"

# Verbose mode: print every command before running it, with its line number
if [[ "$VERBOSE" == true ]]; then
    log "Verbose mode enabled"
    PS4='+ line ${LINENO}: '
    set -x
fi

# --------------------------------------------------
# 5. Check required commands
# --------------------------------------------------

for cmd in curl unzip tar awk tee; do
    require_command "$cmd"
done

command -v sha256sum >/dev/null 2>&1 || command -v shasum >/dev/null 2>&1 \
    || die "Required command not found: sha256sum (or shasum)"

# --------------------------------------------------
# 6. Check Python dependencies
# --------------------------------------------------

find_python
log "Using Python: $(command -v "$PYTHON") ($("$PYTHON" --version 2>&1))"

# --------------------------------------------------
# 7. Prepare dataset
# --------------------------------------------------

[[ -f "$CHECKSUM_FILE" ]] \
    || die "Checksum file is missing: $CHECKSUM_FILE"

prepare_dataset

# --------------------------------------------------
# 8. Shell filtering of the raw data (cut | grep | awk | sort | uniq)
# --------------------------------------------------

cd "$PROJECT_DIR"

run_step "Filtering raw data with shell tools" \
    bash scripts/shell_filter.sh "$ASC_FILE" "$RESULTS_DIR"

# --------------------------------------------------
# 9. Run Python analysis
# --------------------------------------------------

run_step "Running diabetes analysis" \
    "$PYTHON" scripts/reproduce_age_bmi_diabetes.py --input "$ASC_FILE" --output "$RESULTS_DIR/age_bmi_diabetes_python.csv" --chunk-size 50000

# --------------------------------------------------
# 10. Statistical analysis (confidence intervals, chi-square)
# --------------------------------------------------

run_step "Computing statistics" \
    "$PYTHON" scripts/stats_analysis.py --input "$RESULTS_DIR/age_bmi_diabetes_python.csv" --output "$RESULTS_DIR/stats.json"

# --------------------------------------------------
# 11. Generate visualizations
# --------------------------------------------------

run_step "Generating obesity-age graph" \
    "$PYTHON" scripts/plot_obesity_age.py

run_step "Generating BMI-age comparison graph" \
    "$PYTHON" scripts/plot_bmi_age_comparison.py

# --------------------------------------------------
# 12. Display age-group summary using a shell pipeline
# --------------------------------------------------

log "Counting result rows by age group..."

tail -n +2 "$RESULTS_DIR/age_bmi_diabetes_python.csv" \
    | cut -d',' -f1 \
    | sort \
    | uniq -c

# --------------------------------------------------
# 13. Run automated tests
# --------------------------------------------------

if [[ "$SKIP_TESTS" == false ]]; then

    run_step "Running automated tests" \
        "$PYTHON" -m unittest discover -s tests -v

else
    log "Automated tests skipped."
fi

# --------------------------------------------------
# 14. Create dated results archive
# --------------------------------------------------

ARCHIVE_FILE="$ARCHIVE_DIR/results_$(date '+%Y%m%d_%H%M%S').tar.gz"

log "Creating results archive..."

tar -czf "$ARCHIVE_FILE" -C "$PROJECT_DIR" results \
    || die "Could not create results archive."

log "Archive created: $ARCHIVE_FILE"

# --------------------------------------------------
# 15. Finish
# --------------------------------------------------

log "========================================"
log "PROJECT PIPELINE COMPLETED SUCCESSFULLY"
log "Log file: $LOG_FILE"
log "========================================"
