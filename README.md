# Enquête sur une maladie

## Project overview
Exploratory analysis of type 2 diabetes using the CDC BRFSS 2022 dataset.

## Dataset
The raw dataset is not stored in this Git repository because of its size.

Download the official 2022 BRFSS ASCII dataset from:
https://www.cdc.gov/brfss/annual_data/2022/files/LLCP2022ASC.zip

Extract the archive and place `LLCP2022.ASC` inside the `data/` directory.

## Project structure
- `data/` — local dataset (not tracked by Git)
- `docs/` — CDC variable layout documentation
- `results/` — exploratory CSV analysis results
- `scripts/` — analysis scripts
- `tests/` — tests
- `logs/` — logs

## Important note
The current results are exploratory, unweighted analyses. The diabetes-type
classification and applicable state/territory coverage still need validation
against the official CDC documentation before final conclusions are drawn.
