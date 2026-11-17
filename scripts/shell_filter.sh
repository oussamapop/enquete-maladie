#!/usr/bin/env bash

# --------------------------------------------------
# Shell filtering of the raw BRFSS 2022 dataset
#
# Extracts the useful columns from the fixed-width file, keeps the
# 13 reporting areas and the two groups compared (Type 2 / no diabetes),
# then counts each age x BMI x group combination with a pipe:
#
#   cut | grep | awk | sort | uniq -c
#
# From these counts it writes three CSV files:
#   age_bmi_diabetes.csv         Type 2 % by age group x BMI category
#                                (compared with the Python result by the tests)
#   age_diabetes.csv             Type 2 vs no diabetes by age group
#   bmi_diabetes_comparison.csv  BMI distribution of each group
#
# Usage: scripts/shell_filter.sh [INPUT_ASC] [OUTPUT_DIR]
# --------------------------------------------------

set -euo pipefail

# Same byte order and number format on every system
export LC_ALL=C

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

INPUT="${1:-$PROJECT_DIR/data/LLCP2022.ASC}"
OUTPUT_DIR="${2:-$PROJECT_DIR/results}"

# Reporting areas where the Diabetes module (DIABTYPE) was asked
STATES="10|13|18|23|28|29|32|38|45|46|50|55|78"

# --------------------------------------------------
# Functions
# --------------------------------------------------

error() {
    echo "shell_filter.sh: ERROR: $*" >&2
    exit 1
}

# Remove the temporary files (on normal exit and on interruption)
cleanup() {
    rm -f "$COUNTS_FILE" "$OUTPUT_DIR"/.*.csv.tmp
}

# Step 1: one line per record kept, "age,bmi,group", then counted.
#   cut   -> 7 characters: state(2) DIABETE4(1) DIABTYPE(1) _AGEG5YR(2) _BMI5CAT(1)
#            (1-based positions from the CDC variable layout)
#   grep  -> keep the 13 reporting areas
#   awk   -> label the group, drop the other diabetes answers
#   sort | uniq -c -> number of records for each combination
count_records() {
    cut -c1-2,129,271,1981-1982,2002 "$INPUT" \
        | grep -E "^($STATES)" \
        | awk '{
              diabetes = substr($0, 3, 1)
              diabtype = substr($0, 4, 1)
              age      = substr($0, 5, 2)
              bmi      = substr($0, 7, 1)

              if (diabetes == "1" && diabtype == "2") group = "type2"
              else if (diabetes == "3")               group = "none"
              else next

              # Blank (missing) values become "?" so every field stays visible
              gsub(/ /, "?", age)
              gsub(/ /, "?", bmi)

              print age "," bmi "," group
          }' \
        | sort \
        | uniq -c
}

# Step 2: turn the counts into one CSV (summary = grid, age or bmi).
# Writes to a temporary file first, then renames it, so an interrupted
# run never leaves a half-written CSV.
write_summary() {
    local summary="$1"
    local output="$2"
    local temp="$OUTPUT_DIR/.$(basename "$output").tmp"

    awk -v summary="$summary" '
    {
        # Input line: "   COUNT age,bmi,group"
        n = $1
        split($2, field, ",")
        age = field[1]; bmi = field[2]; group = field[3]

        valid_age = (age ~ /^(0[1-9]|1[0-3])$/)
        valid_bmi = (bmi ~ /^[1-4]$/)

        if (valid_age)              by_age[age, group] += n
        if (valid_bmi)              by_bmi[bmi, group] += n
        if (valid_age && valid_bmi) by_grid[age, bmi, group] += n
    }

    END {
        if (summary == "grid") {
            print "age_code,bmi_category,type2_count,no_diabetes_count,total,percentage,small_case_count"
            for (a = 1; a <= 13; a++) {
                age = sprintf("%02d", a)
                for (b = 1; b <= 4; b++) {
                    t2 = by_grid[age, b, "type2"] + 0
                    no = by_grid[age, b, "none"] + 0
                    total = t2 + no
                    if (total == 0) continue
                    printf "%s,%d,%d,%d,%d,%.2f,%s\n", age, b, t2, no, total,
                           100 * t2 / total, (t2 < 20 ? "YES" : "NO")
                }
            }
        }

        if (summary == "age") {
            print "age_code,type2_count,no_diabetes_count,type2_percent"
            for (a = 1; a <= 13; a++) {
                age = sprintf("%02d", a)
                t2 = by_age[age, "type2"] + 0
                no = by_age[age, "none"] + 0
                if (t2 + no == 0) continue
                printf "%s,%d,%d,%.2f\n", age, t2, no, 100 * t2 / (t2 + no)
            }
        }

        if (summary == "bmi") {
            print "group,category,count,percentage,total_valid_bmi"
            split("none type2", groups, " ")
            split("no_diabetes type2", names, " ")
            for (g = 1; g <= 2; g++) {
                total = 0
                for (b = 1; b <= 4; b++) total += by_bmi[b, groups[g]]
                if (total == 0) continue
                for (b = 1; b <= 4; b++) {
                    n = by_bmi[b, groups[g]] + 0
                    printf "%s,%d,%d,%.2f,%d\n", names[g], b, n, 100 * n / total, total
                }
            }
        }
    }' "$COUNTS_FILE" > "$temp"

    mv -f "$temp" "$output"
    echo "Written: $output"
}

# --------------------------------------------------
# Main
# --------------------------------------------------

[[ -f "$INPUT" ]] || error "Dataset not found: $INPUT"
[[ -s "$INPUT" ]] || error "Dataset is empty: $INPUT"

mkdir -p "$OUTPUT_DIR"

COUNTS_FILE="$(mktemp "${TMPDIR:-/tmp}/shell_filter.XXXXXX")"
trap cleanup EXIT
trap 'echo "shell_filter.sh: interrupted" >&2; exit 130' INT TERM

echo "Filtering $INPUT with cut | grep | awk | sort | uniq -c ..."
# grep returns 1 when nothing matches: with pipefail the whole pipe fails
count_records > "$COUNTS_FILE" \
    || error "No record matched the filter (check the input file)."

echo "Combinations counted: $(wc -l < "$COUNTS_FILE")"

write_summary grid "$OUTPUT_DIR/age_bmi_diabetes.csv"
write_summary age  "$OUTPUT_DIR/age_diabetes.csv"
write_summary bmi  "$OUTPUT_DIR/bmi_diabetes_comparison.csv"
