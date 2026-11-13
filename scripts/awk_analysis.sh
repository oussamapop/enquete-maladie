#!/usr/bin/env bash

# --------------------------------------------------
# Bash/AWK analysis of the BRFSS 2022 dataset
#
# Reads the fixed-width file once and writes three summaries:
#   results/age_diabetes.csv            Type 2 vs no diabetes by age group
#   results/bmi_diabetes_comparison.csv BMI distribution of each group
#   results/age_bmi_diabetes.csv        Type 2 % by age group x BMI category
#
# age_bmi_diabetes.csv is compared with the Python version by the tests.
#
# Usage: scripts/awk_analysis.sh [INPUT_ASC] [OUTPUT_DIR]
# --------------------------------------------------

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

INPUT="${1:-$PROJECT_DIR/data/LLCP2022.ASC}"
OUTPUT_DIR="${2:-$PROJECT_DIR/results}"

[[ -s "$INPUT" ]] || { echo "Dataset not found: $INPUT" >&2; exit 1; }
mkdir -p "$OUTPUT_DIR"

LC_ALL=C awk \
    -v age_out="$OUTPUT_DIR/age_diabetes.csv" \
    -v bmi_out="$OUTPUT_DIR/bmi_diabetes_comparison.csv" \
    -v grid_out="$OUTPUT_DIR/age_bmi_diabetes.csv" '

BEGIN {
    # Reporting areas where the Diabetes module (DIABTYPE) was asked
    split("10 13 18 23 28 29 32 38 45 46 50 55 78", codes, " ")
    for (i in codes) selected[codes[i]] = 1
}

{
    # Fixed-width positions (CDC variable layout, 1-based)
    state    = substr($0, 1, 2)
    diabetes = substr($0, 129, 1)     # DIABETE4
    diabtype = substr($0, 271, 1)     # DIABTYPE
    age      = substr($0, 1981, 2)    # _AGEG5YR
    bmi      = substr($0, 2002, 1)    # _BMI5CAT

    if (!(state in selected)) next

    # 1 = Type 2 diabetes, 0 = no diabetes, other answers are excluded
    if (diabetes == "1" && diabtype == "2") group = 1
    else if (diabetes == "3")               group = 0
    else next

    valid_age = (age >= "01" && age <= "13" && age ~ /^[0-9][0-9]$/)
    valid_bmi = (bmi ~ /^[1-4]$/)

    if (valid_age) age_count[age, group]++
    if (valid_bmi) bmi_count[bmi, group]++
    if (valid_age && valid_bmi) grid_count[age, bmi, group]++
}

END {
    # Type 2 vs no diabetes by age group
    print "age_code,type2_count,no_diabetes_count,type2_percent" > age_out
    for (a = 1; a <= 13; a++) {
        age = sprintf("%02d", a)
        t2 = age_count[age, 1] + 0
        no = age_count[age, 0] + 0
        if (t2 + no == 0) continue
        printf "%s,%d,%d,%.2f\n", age, t2, no, 100 * t2 / (t2 + no) > age_out
    }

    # BMI category distribution of each group
    for (b = 1; b <= 4; b++) {
        bmi_total[0] += bmi_count[b, 0]
        bmi_total[1] += bmi_count[b, 1]
    }
    print "group,category,count,percentage,total_valid_bmi" > bmi_out
    split("no_diabetes type2", names, " ")
    for (g = 0; g <= 1; g++) {
        if (bmi_total[g] == 0) continue
        for (b = 1; b <= 4; b++) {
            n = bmi_count[b, g] + 0
            printf "%s,%d,%d,%.2f,%d\n", names[g + 1], b, n, 100 * n / bmi_total[g], bmi_total[g] > bmi_out
        }
    }

    # Type 2 % by age group x BMI category
    print "age_code,bmi_category,type2_count,no_diabetes_count,total,percentage,small_case_count" > grid_out
    for (a = 1; a <= 13; a++) {
        age = sprintf("%02d", a)
        for (b = 1; b <= 4; b++) {
            t2 = grid_count[age, b, 1] + 0
            no = grid_count[age, b, 0] + 0
            total = t2 + no
            if (total == 0) continue
            printf "%s,%d,%d,%d,%d,%.2f,%s\n", age, b, t2, no, total, 100 * t2 / total, (t2 < 20 ? "YES" : "NO") > grid_out
        }
    }
}
' "$INPUT"

echo "AWK results written to: $OUTPUT_DIR"
