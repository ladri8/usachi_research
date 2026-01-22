# USACHI Research Project

Clinical research data analysis project (CTSI 7435).

## Project Structure

### Data Quality
- `00_phase0_data_quality_audit.ipynb` - Data quality audit notebook
- `00_phase0_data_quality_script.py` - Automated data quality checks
- `DATA_QUALITY_REPORT.md` - Data quality assessment documentation

### Phase 0 Analysis
- `01_phase0_representation.ipynb` - Data representation analysis
- `02_phase0_report.ipynb` - Phase 0 comprehensive report
- `03_phase0_arrival_period_analysis.qmd` - Arrival period analysis (Quarto)

### Data Files
- CSV data files with labels (ignored in git for privacy)
- Sample data: `phase0_analysis_sample.csv`

## Setup

1. Install required Python packages:
   ```bash
   pip install pandas numpy jupyter plotly
   ```

2. Install Quarto for report generation (optional):
   ```bash
   # Follow instructions at https://quarto.org/docs/get-started/
   ```

## Usage

Run Jupyter notebooks for interactive analysis:
```bash
jupyter notebook
```

Generate Quarto reports:
```bash
quarto render <filename>.qmd
```

## Notes

- Data files (.csv) are excluded from version control
- HTML reports are generated outputs and not tracked in git
