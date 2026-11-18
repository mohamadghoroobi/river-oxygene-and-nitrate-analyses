# River water quality: oxygen and nitrate

This project studies how oxygen and nitrate concentrations change across seasons and along a river. It compares spring with autumn, then checks which river sections have different average concentrations. Saubach is the river name.

## Data

The dataset comes from [TU Dortmund University](https://statistik.tu-dortmund.de/storages/statistik/r/Downloads/Studium/Studiengaenge-Infos/Data_Science/waterquality.csv). It contains 900 observations from five river sections, from headwaters to mouth, across spring, summer, autumn, and winter. There are 180 observations per section and 45 per section in each season.

The original file is in `data/raw/waterquality.csv`. Both concentrations are measured in milligrams per liter (mg/L).

| Column | Description |
|---|---|
| `ID` | Observation number |
| `river_section` | Section of the river |
| `saison` | Season |
| `oxygen_mgL` | Oxygen concentration in mg/L |
| `nitrate_mgL` | Nitrate concentration in mg/L |

## Run the analysis

Install Python 3.12, then open a terminal in the project folder. On Windows, run these commands in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe src/download_data.py
.\.venv\Scripts\python.exe src/analyze.py
.\.venv\Scripts\python.exe src/inference.py
.\.venv\Scripts\python.exe src/validate_outputs.py
```

On macOS or Linux, replace `.\.venv\Scripts\python.exe` with `.venv/bin/python`.

The download script keeps the existing dataset if it is already present. The analysis saves summary tables and test results in `outputs/tables/`, and plots in `outputs/figures/`. The validation script checks the results against the original data.

You can also explore the results in [the notebook](notebooks/01_exploration.ipynb), using a Jupyter-compatible editor with the project environment selected.

## Report

- [Read the 10-page report](report/river_water_quality_report.pdf).
- [Download the editable Overleaf project](report/saubach_overleaf.zip).
