#!/usr/bin/env python3
"""
Tests of the processing itself, on a small synthetic fixed-width file.

They do not need the 914 MB dataset: each test builds a few BRFSS-like
records (2052 characters, values at the CDC positions) whose expected
result is known in advance.
"""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from reproduce_age_bmi_diabetes import build_results, count_groups  # noqa: E402
from stats_analysis import chi_square_test, chi_square_p_value, wilson_interval  # noqa: E402


RECORD_LENGTH = 2052

# Full path of bash (on Windows, a bare "bash" could start WSL instead of Git Bash)
BASH = shutil.which("bash")


def make_record(state, diabetes, diabtype, age, bmi):
    """One fixed-width record, values placed at the CDC 1-based positions."""
    line = [" "] * RECORD_LENGTH
    for position, value in [(1, state), (129, diabetes), (271, diabtype),
                            (1981, age), (2002, bmi)]:
        for offset, char in enumerate(value):
            line[position - 1 + offset] = char
    return "".join(line)


# Synthetic sample: expected result = 2 groups
#   age 05 x BMI 4: 2 Type 2, 1 no diabetes
#   age 10 x BMI 2: 1 Type 2, 2 no diabetes
SAMPLE = [
    make_record("13", "1", "2", "05", "4"),   # Type 2, kept
    make_record("13", "1", "2", "05", "4"),   # Type 2, kept
    make_record("55", "3", " ", "05", "4"),   # no diabetes, kept
    make_record("78", "1", "2", "10", "2"),   # Type 2, kept
    make_record("10", "3", " ", "10", "2"),   # no diabetes, kept
    make_record("10", "3", " ", "10", "2"),   # no diabetes, kept
    make_record("01", "1", "2", "05", "4"),   # excluded: state not selected
    make_record("13", "1", "1", "05", "4"),   # excluded: Type 1
    make_record("13", "4", " ", "05", "4"),   # excluded: prediabetes
    make_record("13", "3", " ", "14", "4"),   # excluded: age unknown (14)
    make_record("13", "3", " ", "05", " "),   # excluded: BMI missing
]


class SampleFileTestCase(unittest.TestCase):
    """Writes the synthetic sample to a temporary directory."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.sample_file = self.temp_dir / "sample.asc"
        self.sample_file.write_text("\n".join(SAMPLE) + "\n", encoding="ascii")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)


class TestCountGroups(SampleFileTestCase):

    # Test 1: the pattern keeps exactly the expected records
    def test_counts(self):
        counts, stats = count_groups(self.sample_file, chunk_size=4)

        self.assertEqual(counts, {
            ("05", "4"): {"type2_count": 2, "no_diabetes_count": 1},
            ("10", "2"): {"type2_count": 1, "no_diabetes_count": 2},
        })
        self.assertEqual(stats["total_records"], len(SAMPLE))
        self.assertEqual(stats["selected_records"], len(SAMPLE) - 1)
        self.assertEqual(stats["valid_records"], 6)

    # Test 2: the chunk size does not change the result
    def test_chunk_size_independent(self):
        small, _ = count_groups(self.sample_file, chunk_size=1)
        large, _ = count_groups(self.sample_file, chunk_size=1000)
        self.assertEqual(small, large)

    # Test 3: totals, percentages and small-count flag of the results table
    def test_build_results(self):
        counts, _ = count_groups(self.sample_file, chunk_size=4)
        results = build_results(counts)

        self.assertEqual(list(results["total"]), [3, 3])
        self.assertEqual(list(results["percentage"]), [66.67, 33.33])
        self.assertEqual(list(results["small_case_count"]), ["YES", "YES"])


class TestShellFilter(SampleFileTestCase):

    # Test 4: the shell pipe (cut | grep | awk | sort | uniq) gives the same
    # table as Python on the same input
    @unittest.skipUnless(BASH, "bash is not available")
    def test_shell_matches_python(self):
        subprocess.run(
            [BASH, (SCRIPTS_DIR / "shell_filter.sh").as_posix(),
             self.sample_file.as_posix(), self.temp_dir.as_posix()],
            check=True, capture_output=True,
        )

        shell = pd.read_csv(self.temp_dir / "age_bmi_diabetes.csv", dtype={"age_code": str})
        counts, _ = count_groups(self.sample_file, chunk_size=4)
        python = build_results(counts)
        python["bmi_category"] = python["bmi_category"].astype(int)

        pd.testing.assert_frame_equal(shell, python)

    # Test 5: a missing input file gives a non-zero exit code and a message
    @unittest.skipUnless(BASH, "bash is not available")
    def test_shell_missing_file(self):
        result = subprocess.run(
            [BASH, (SCRIPTS_DIR / "shell_filter.sh").as_posix(),
             (self.temp_dir / "missing.asc").as_posix(), self.temp_dir.as_posix()],
            capture_output=True, text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Dataset not found", result.stderr)


class TestStatistics(unittest.TestCase):

    # Test 6: Wilson interval against a known value (10 / 100 -> 5.52 % - 17.44 %)
    def test_wilson_interval(self):
        self.assertEqual(wilson_interval(10, 100), (5.52, 17.44))

    # Test 7: the interval stays within 0-100 % even with 0 cases
    def test_wilson_bounds(self):
        low, high = wilson_interval(0, 50)
        self.assertEqual(low, 0.0)
        self.assertTrue(0 < high < 100)

    # Test 8: chi-square = 0 when Type 2 does not depend on the category
    def test_chi_square_independent(self):
        table = pd.DataFrame({"type2_count": [10, 20], "no_diabetes_count": [90, 180]})
        statistic, dof, p_value = chi_square_test(table)
        self.assertAlmostEqual(statistic, 0.0)
        self.assertEqual(dof, 1)
        self.assertGreater(p_value, 0.5)

    # Test 9: p-value close to the 5 % table values (7.815 with 3 df, 21.026 with 12 df)
    def test_chi_square_p_value(self):
        self.assertAlmostEqual(chi_square_p_value(7.815, 3), 0.05, delta=0.003)
        self.assertAlmostEqual(chi_square_p_value(21.026, 12), 0.05, delta=0.003)


if __name__ == "__main__":
    unittest.main()
