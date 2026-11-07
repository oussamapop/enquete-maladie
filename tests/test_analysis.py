from pathlib import Path
import unittest
import pandas as pd


# --------------------------------------------------
# Project paths
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_DIR / "results"

AWK_FILE = RESULTS_DIR / "age_bmi_diabetes.csv"
PYTHON_FILE = RESULTS_DIR / "age_bmi_diabetes_python.csv"


EXPECTED_COLUMNS = [
    "age_code",
    "bmi_category",
    "type2_count",
    "no_diabetes_count",
    "total",
    "percentage",
    "small_case_count",
]


class TestDiabetesAnalysis(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.awk = pd.read_csv(AWK_FILE)
        cls.python = pd.read_csv(PYTHON_FILE)

    # Test 1: Check the CSV structure
    def test_columns(self):
        self.assertEqual(list(self.python.columns), EXPECTED_COLUMNS)

    # Test 2: Check the number of age-BMI groups
    def test_number_of_groups(self):
        self.assertEqual(len(self.python), 52)

    # Test 3: Check valid age categories
    def test_age_categories(self):
        valid_ages = [str(i).zfill(2) for i in range(1, 14)]
        ages = self.python["age_code"].astype(str).str.zfill(2)

        self.assertTrue(ages.isin(valid_ages).all())

    # Test 4: Check valid BMI categories
    def test_bmi_categories(self):
        valid_bmi = [1, 2, 3, 4]

        self.assertTrue(
            self.python["bmi_category"].isin(valid_bmi).all()
        )

    # Test 5: Check total calculations
    def test_total_calculation(self):
        calculated_total = (
            self.python["type2_count"]
            + self.python["no_diabetes_count"]
        )

        self.assertTrue(
            (calculated_total == self.python["total"]).all()
        )

    # Test 6: Check percentage calculations
    def test_percentage_calculation(self):
        expected = (
            self.python["type2_count"]
            / self.python["total"]
            * 100
        ).round(2)

        self.assertTrue(
            (expected == self.python["percentage"]).all()
        )

    # Test 7: Check small case classification
    def test_small_case_count(self):
        expected = self.python["type2_count"].apply(
            lambda count: "YES" if count < 20 else "NO"
        )

        self.assertTrue(
            (expected == self.python["small_case_count"]).all()
        )

    # Test 8: Check overall diabetes counts
    def test_overall_counts(self):
        self.assertEqual(
            int(self.python["type2_count"].sum()),
            9393
        )

        self.assertEqual(
            int(self.python["no_diabetes_count"].sum()),
            67126
        )

    # Test 9: Check AWK and Python results are identical
    def test_awk_python_consistency(self):
        awk = self.awk[EXPECTED_COLUMNS].sort_values(
            ["age_code", "bmi_category"]
        ).reset_index(drop=True)

        python = self.python[EXPECTED_COLUMNS].sort_values(
            ["age_code", "bmi_category"]
        ).reset_index(drop=True)

        pd.testing.assert_frame_equal(awk, python)


if __name__ == "__main__":
    unittest.main()