#!/usr/bin/env bash

# Stop if any command fails
set -euo pipefail

# --------------------------------------------------
# 1. Project configuration
# --------------------------------------------------

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

DATA_DIR="$PROJECT_DIR/data"
RESULTS_DIR="$PROJECT_DIR/results"
LOG_DIR="$PROJECT_DIR/logs"
ARCHIVE_DIR="$PROJECT_DIR/archive"

ZIP_FILE="$DATA_DIR/LLCP2022ASC.zip"
ASC_FILE="$DATA_DIR/LLCP2022.ASC"
CHECKSUM_FILE="$PROJECT_DIR/checksums/LLCP2022ASC.zip.sha256"

DATA_URL="https://www.cdc.gov/brfss/annual_data/2022/files/LLCP2022ASC.zip"

FORCE_DOWNLOAD=false
SKIP_TESTS=false

# --------------------------------------------------
# 2. Functions
# --------------------------------------------------

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

die() {
    log "ERROR: $*"
    exit 1
}

require_command() {
    command -v "$1" >/dev/null 2>&1 || die "Required command not found: $1"
}

show_help() {
    cat <<HELP
Usage: ./run.sh [OPTIONS]

Options:
  -h    Display this help message
  -f    Force dataset download
  -s    Skip automated tests

Examples:
  ./run.sh
  ./run.sh -f
  ./run.sh -s
HELP
}

verify_checksum() {
    local file="$1"
    local expected actual

    expected="$(awk '{print $1}' "$CHECKSUM_FILE")"
    actual="$(sha256sum "$file" | awk '{print $1}')"

    if [[ "$actual" != "$expected" ]]; then
        return 1
    fi

    return 0
}

download_dataset() {
    local temp_file="$ZIP_FILE.tmp"

    log "Downloading BRFSS 2022 dataset..."

    rm -f "$temp_file"

    curl -fL --retry 3 \
        --output "$temp_file" \
        "$DATA_URL" || die "Dataset download failed."

    log "Verifying downloaded dataset checksum..."

    if ! verify_checksum "$temp_file"; then
        rm -f "$temp_file"
        die "Checksum verification failed. Downloaded file does not match the expected SHA256."
    fi

    unzip -tq "$temp_file" || die "Downloaded ZIP archive is invalid."

    mv "$temp_file" "$ZIP_FILE"

    log "Dataset downloaded and verified successfully."
}

prepare_dataset() {

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

    log "Dataset is ready."
}

run_step() {
    local description="$1"
    shift

    log "$description"
    "$@"
    log "Completed: $description"
}

# --------------------------------------------------
# 3. Read command-line options
# --------------------------------------------------

while getopts ":hfs" option; do
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

exec > >(tee -a "$LOG_FILE") 2>&1

log "========================================"
log "Starting Enquête sur une maladie"
log "========================================"

# --------------------------------------------------
# 5. Check required commands
# --------------------------------------------------

for cmd in python3 curl unzip sha256sum tar awk tee; do
    require_command "$cmd"
done

# --------------------------------------------------
# 6. Check Python dependencies
# --------------------------------------------------

python3 -c "import pandas, numpy, matplotlib" \
    || die "Python dependencies are missing. Run: python3 -m pip install -r requirements.txt"

# --------------------------------------------------
# 7. Prepare dataset
# --------------------------------------------------

[[ -f "$CHECKSUM_FILE" ]] \
    || die "Checksum file is missing: $CHECKSUM_FILE"

prepare_dataset

# --------------------------------------------------
# 8. Run Python analysis
# --------------------------------------------------

cd "$PROJECT_DIR"

run_step "Running diabetes analysis" \
    python3 scripts/reproduce_age_bmi_diabetes.py --input "$ASC_FILE" --output "$RESULTS_DIR/age_bmi_diabetes_python.csv" --chunk-size 50000

# --------------------------------------------------
# 9. Generate visualizations
# --------------------------------------------------

run_step "Generating obesity-age graph" \
    python3 scripts/plot_obesity_age.py

run_step "Generating BMI-age comparison graph" \
    python3 scripts/plot_bmi_age_comparison.py

# --------------------------------------------------
# 10. Display age-group summary using a shell pipeline
# --------------------------------------------------

log "Counting result rows by age group..."

tail -n +2 "$RESULTS_DIR/age_bmi_diabetes_python.csv" \
    | cut -d',' -f1 \
    | sort \
    | uniq -c

# --------------------------------------------------
# 11. Run automated tests
# --------------------------------------------------

if [[ "$SKIP_TESTS" == false ]]; then

    run_step "Running automated tests" \
        python3 -m unittest discover -s tests -v

else
    log "Automated tests skipped."
fi

# --------------------------------------------------
# 12. Create dated results archive
# --------------------------------------------------

ARCHIVE_FILE="$ARCHIVE_DIR/results_$(date '+%Y%m%d_%H%M%S').tar.gz"

log "Creating results archive..."

tar -czf "$ARCHIVE_FILE" -C "$PROJECT_DIR" results \
    || die "Could not create results archive."

log "Archive created: $ARCHIVE_FILE"

# --------------------------------------------------
# 13. Finish
# --------------------------------------------------

log "========================================"
log "PROJECT PIPELINE COMPLETED SUCCESSFULLY"
log "Log file: $LOG_FILE"
log "========================================"
