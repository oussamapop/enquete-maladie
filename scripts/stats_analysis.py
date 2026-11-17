#!/usr/bin/env python3
"""
Statistical analysis of the age x BMI results.

Reads results/age_bmi_diabetes_python.csv and writes results/stats.json with:
  - the 95% Wilson confidence interval of the Type 2 percentage of each group;
  - for each age group, the ratio "Type 2 % if obese / Type 2 % if normal BMI";
  - two chi-square tests of independence: Type 2 vs BMI category,
    and Type 2 vs age group.

Only pandas and the standard library are used (no SciPy).
"""

import argparse
import json
import math
import sys
from pathlib import Path

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent.parent

AGE_LABELS = {
    "01": "18-24", "02": "25-29", "03": "30-34", "04": "35-39",
    "05": "40-44", "06": "45-49", "07": "50-54", "08": "55-59",
    "09": "60-64", "10": "65-69", "11": "70-74", "12": "75-79",
    "13": "80+",
}

BMI_LABELS = {1: "underweight", 2: "normal", 3: "overweight", 4: "obese"}


# --------------------------------------------------
# 1. Command-line arguments (argparse)
# --------------------------------------------------

def parse_arguments():

    parser = argparse.ArgumentParser(
        description="Confidence intervals and chi-square tests on the age x BMI results."
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=PROJECT_DIR / "results" / "age_bmi_diabetes_python.csv",
        help="Results CSV produced by reproduce_age_bmi_diabetes.py.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_DIR / "results" / "stats.json",
        help="Path of the JSON file to write.",
    )

    parser.add_argument(
        "--z",
        type=float,
        default=1.96,
        help="z value of the confidence level (default: 1.96 for 95%%).",
    )

    args = parser.parse_args()

    if args.z <= 0:
        parser.error("--z must be greater than zero.")

    return args


# --------------------------------------------------
# 2. Statistical functions
# --------------------------------------------------

def wilson_interval(cases, total, z=1.96):
    """
    Wilson confidence interval of a proportion cases / total, in percent.
    Better than the usual p +/- z*sqrt(p(1-p)/n) for small counts or
    proportions close to 0 (it never goes below 0 or above 100).
    """
    if total <= 0:
        raise ValueError("total must be greater than zero")

    p = cases / total
    denominator = 1 + z**2 / total
    center = (p + z**2 / (2 * total)) / denominator
    half_width = (z / denominator) * math.sqrt(
        p * (1 - p) / total + z**2 / (4 * total**2)
    )

    low = max(0.0, center - half_width)
    high = min(1.0, center + half_width)

    return round(low * 100, 2), round(high * 100, 2)


def chi_square_test(table):
    """
    Chi-square test of independence on a contingency table
    (DataFrame: one row per category, columns = type2_count, no_diabetes_count).

    Returns the statistic, the degrees of freedom and an approximate p-value
    (Wilson-Hilferty approximation of the chi-square distribution).
    """
    observed = table.to_numpy(dtype=float)
    row_totals = observed.sum(axis=1, keepdims=True)
    column_totals = observed.sum(axis=0, keepdims=True)
    grand_total = observed.sum()

    # Expected counts if Type 2 did not depend on the category
    expected = row_totals * column_totals / grand_total

    statistic = float(((observed - expected) ** 2 / expected).sum())
    dof = (observed.shape[0] - 1) * (observed.shape[1] - 1)

    return statistic, dof, chi_square_p_value(statistic, dof)


def chi_square_p_value(statistic, dof):
    """
    P(Chi2(dof) > statistic), Wilson-Hilferty approximation:
    (X / dof)^(1/3) is close to a normal law of mean 1 - 2/(9 dof)
    and variance 2/(9 dof).
    """
    if dof <= 0:
        return 1.0

    mean = 1 - 2 / (9 * dof)
    std = math.sqrt(2 / (9 * dof))
    z = ((statistic / dof) ** (1 / 3) - mean) / std

    return 0.5 * math.erfc(z / math.sqrt(2))


# --------------------------------------------------
# 3. Analysis
# --------------------------------------------------

def load_results(input_file):
    df = pd.read_csv(input_file, dtype={"age_code": str})
    df["age_code"] = df["age_code"].str.zfill(2)
    return df


def group_intervals(df, z):
    """One entry per age x BMI group, with its confidence interval."""
    groups = []

    for row in df.itertuples(index=False):
        low, high = wilson_interval(row.type2_count, row.total, z)
        groups.append({
            "age_code": row.age_code,
            "age_group": AGE_LABELS.get(row.age_code, row.age_code),
            "bmi_category": int(row.bmi_category),
            "bmi_label": BMI_LABELS.get(int(row.bmi_category), "unknown"),
            "type2_count": int(row.type2_count),
            "total": int(row.total),
            "percentage": float(row.percentage),
            "ci_low": low,
            "ci_high": high,
            "small_case_count": row.small_case_count,
        })

    return groups


def obese_vs_normal(df):
    """For each age group: Type 2 % of obese / Type 2 % of normal BMI."""
    ratios = []

    for age, group in df.groupby("age_code", sort=True):
        by_bmi = group.set_index("bmi_category")
        if 2 not in by_bmi.index or 4 not in by_bmi.index:
            continue

        normal = by_bmi.loc[2]
        obese = by_bmi.loc[4]

        normal_pct = normal["type2_count"] / normal["total"] * 100
        obese_pct = obese["type2_count"] / obese["total"] * 100

        ratios.append({
            "age_code": age,
            "age_group": AGE_LABELS.get(age, age),
            "normal_percentage": round(normal_pct, 2),
            "obese_percentage": round(obese_pct, 2),
            "ratio": round(obese_pct / normal_pct, 2) if normal_pct > 0 else None,
            "reliable": bool(normal["type2_count"] >= 20 and obese["type2_count"] >= 20),
        })

    return ratios


def chi_square_by(df, column):
    """Chi-square test of Type 2 against one variable (age_code or bmi_category)."""
    table = df.groupby(column)[["type2_count", "no_diabetes_count"]].sum()
    statistic, dof, p_value = chi_square_test(table)

    return {
        "variable": column,
        "statistic": round(statistic, 2),
        "degrees_of_freedom": dof,
        "p_value": p_value,
        "significant_at_5_percent": p_value < 0.05,
    }


def analyse(df, z=1.96):
    type2 = int(df["type2_count"].sum())
    total = int(df["total"].sum())
    low, high = wilson_interval(type2, total, z)

    return {
        "source": "BRFSS 2022, 13 reporting areas, unweighted counts",
        "z": z,
        "overall": {
            "type2_count": type2,
            "total": total,
            "percentage": round(type2 / total * 100, 2),
            "ci_low": low,
            "ci_high": high,
        },
        "chi_square": [
            chi_square_by(df, "bmi_category"),
            chi_square_by(df, "age_code"),
        ],
        "obese_vs_normal_by_age": obese_vs_normal(df),
        "groups": group_intervals(df, z),
    }


# --------------------------------------------------
# 4. Main
# --------------------------------------------------

def main():
    args = parse_arguments()

    if not args.input.is_file():
        print(f"Error: results file not found: {args.input}", file=sys.stderr)
        print("Run the analysis first (./run.sh).", file=sys.stderr)
        sys.exit(1)

    stats = analyse(load_results(args.input), args.z)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(stats, handle, indent=2)

    overall = stats["overall"]
    print(f"Type 2 overall: {overall['percentage']} % "
          f"(CI {overall['ci_low']}-{overall['ci_high']} %)")
    for test in stats["chi_square"]:
        print(f"Chi-square Type 2 vs {test['variable']}: "
              f"{test['statistic']} (df={test['degrees_of_freedom']}, "
              f"p={test['p_value']:.3g})")
    print(f"Statistics saved to: {args.output}")


if __name__ == "__main__":
    main()
