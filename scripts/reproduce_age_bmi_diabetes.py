
import argparse
import sys
from pathlib import Path

import pandas as pd


# --------------------------------------------------
# 1. Project paths
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent.parent


# --------------------------------------------------
# 2. Command-line arguments (argparse)
# --------------------------------------------------

def parse_arguments():

    parser = argparse.ArgumentParser(
        description="Analyze BRFSS 2022 diabetes data by age and BMI."
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=PROJECT_DIR / "data" / "LLCP2022.ASC",
        help="Path to the BRFSS ASCII dataset."
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_DIR / "results" / "age_bmi_diabetes_python.csv",
        help="Path where the analysis CSV will be saved."
    )

    parser.add_argument(
        "--chunk-size",
        type=int,
        default=50_000,
        help="Number of records processed per chunk (default: 50000)."
    )

    args = parser.parse_args()

    if args.chunk_size <= 0:
        parser.error("--chunk-size must be greater than zero.")

    return args


# --------------------------------------------------
# 3. BRFSS 2022 fixed-width variable positions
# --------------------------------------------------

COLSPECS = [
    (0, 2),        # State
    (128, 129),    # DIABETE4
    (270, 271),    # DIABTYPE
    (1980, 1982),  # _AGEG5YR
    (2001, 2002),  # _BMI5CAT
]

COLUMNS = [
    "state",
    "diabetes",
    "diabtype",
    "age_code",
    "bmi_category",
]


# --------------------------------------------------
# 4. Analysis settings
# --------------------------------------------------

SELECTED_STATES = [
    "10", "13", "18", "23", "28", "29", "32",
    "38", "45", "46", "50", "55", "78"
]

VALID_AGES = [f"{i:02d}" for i in range(1, 14)]

VALID_BMI = ["1", "2", "3", "4"]


# --------------------------------------------------
# 5. Main analysis function
# --------------------------------------------------

def main():

    args = parse_arguments()

    input_file = args.input
    output_file = args.output
    chunk_size = args.chunk_size

    # Check whether the input dataset exists
    if not input_file.is_file():
        raise FileNotFoundError(
            f"Dataset not found: {input_file}\n"
            "Make sure LLCP2022.ASC exists at the specified location."
        )

    # Create output directory if necessary
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------
    # 6. Process the dataset in chunks
    # --------------------------------------------------

    counts = {}

    total_records = 0
    selected_records = 0
    valid_records = 0

    print("Starting BRFSS 2022 analysis...")
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    print(f"Chunk size: {chunk_size}")

    for chunk in pd.read_fwf(
        input_file,
        colspecs=COLSPECS,
        names=COLUMNS,
        dtype=str,
        keep_default_na=False,
        chunksize=chunk_size,
    ):

        total_records += len(chunk)

        # Keep only the selected states
        selected = chunk[
            chunk["state"].isin(SELECTED_STATES)
        ].copy()

        selected_records += len(selected)

        # Identify Type 2 diabetes and no-diabetes records
        type2_mask = (
            (selected["diabetes"] == "1")
            & (selected["diabtype"] == "2")
        )

        no_diabetes_mask = (
            selected["diabetes"] == "3"
        )

        # Keep only valid age and BMI categories
        valid_age = selected["age_code"].isin(VALID_AGES)

        valid_bmi = selected["bmi_category"].isin(VALID_BMI)

        valid_mask = (
            (type2_mask | no_diabetes_mask)
            & valid_age
            & valid_bmi
        )

        valid = selected.loc[valid_mask].copy()

        valid_records += len(valid)

        if valid.empty:
            continue

        # 1 = Type 2 diabetes, 0 = no diabetes
        valid["is_type2"] = (
            (valid["diabetes"] == "1")
            & (valid["diabtype"] == "2")
        ).astype(int)

        # Count records for each age and BMI combination
        grouped = valid.groupby(
            ["age_code", "bmi_category"],
            sort=True
        )["is_type2"].agg(["sum", "count"])

        for (age, bmi), values in grouped.iterrows():

            key = (age, bmi)

            if key not in counts:
                counts[key] = {
                    "type2_count": 0,
                    "no_diabetes_count": 0,
                }

            type2_count = int(values["sum"])

            total_count = int(values["count"])

            no_diabetes_count = total_count - type2_count

            counts[key]["type2_count"] += type2_count

            counts[key]["no_diabetes_count"] += no_diabetes_count

    # --------------------------------------------------
    # 7. Build the final results table
    # --------------------------------------------------

    results = []

    for (age, bmi), values in sorted(counts.items()):

        type2_count = values["type2_count"]

        no_diabetes_count = values["no_diabetes_count"]

        total = type2_count + no_diabetes_count

        percentage = round(
            (type2_count / total) * 100,
            2
        )

        small_case_count = (
            "YES" if type2_count < 20 else "NO"
        )

        results.append({
            "age_code": age,
            "bmi_category": bmi,
            "type2_count": type2_count,
            "no_diabetes_count": no_diabetes_count,
            "total": total,
            "percentage": percentage,
            "small_case_count": small_case_count,
        })

    # --------------------------------------------------
    # 8. Save the results
    # --------------------------------------------------

    results_df = pd.DataFrame(
        results,
        columns=[
            "age_code",
            "bmi_category",
            "type2_count",
            "no_diabetes_count",
            "total",
            "percentage",
            "small_case_count",
        ],
    )

    results_df.to_csv(output_file, index=False)

    # --------------------------------------------------
    # 9. Display analysis summary
    # --------------------------------------------------

    total_type2 = results_df["type2_count"].sum()

    total_no_diabetes = results_df["no_diabetes_count"].sum()

    print("\nAnalysis completed successfully.")
    print("----------------------------------")
    print(f"Total records: {total_records}")
    print(f"Records in selected states: {selected_records}")
    print(f"Valid records used: {valid_records}")
    print(f"Type 2 cases: {total_type2}")
    print(f"No diabetes cases: {total_no_diabetes}")
    print(f"Number of age-BMI groups: {len(results_df)}")
    print(f"\nResults saved to: {output_file}")


# --------------------------------------------------
# 10. Program entry point
# --------------------------------------------------

if __name__ == "__main__":

    try:
        main()

    except FileNotFoundError as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
