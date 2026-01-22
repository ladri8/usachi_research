import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from great_tables import GT

print("="*80)
print("PHASE 0: DATA QUALITY & CLEANING AUDIT")
print("="*80)

# ==============================================================================
# STEP 1: Load Raw Data
# ==============================================================================
df_raw = pd.read_csv("USACHICTSI7435_DATA_LABELS_2025-12-02_1515.csv")

cohort_flow = []
n_initial = len(df_raw)

cohort_flow.append({
    'Stage': '1. Raw data loaded',
    'N': n_initial,
    'Excluded': 0,
    'Reason': 'Initial load'
})

print(f"\n📊 INITIAL DATA STATE")
print(f"-" * 60)
print(f"Participants: {n_initial}")
print(f"Variables: {len(df_raw.columns)}")

# ==============================================================================
# STEP 2: Data Cleaning
# ==============================================================================
df = df_raw.copy()

# Clean column names
df.columns = df.columns.astype(str)
df.columns = df.columns.str.replace("'", "")
df.columns = df.columns.str.replace('\xa0', ' ')
df.columns = df.columns.str.strip()
df.columns = df.columns.str.lower()

# Rename key variables
rename_dict = {
    "survey date": "survey_date",
    "what is your age?": "age",
    "what is your biological sex?": "sex",
    "what is your household income?": "income",
    "in what year did you or your family arrive to the united states?": "year_arrived_us"
}

df = df.rename(columns=rename_dict)

# Select variables
core_cols = ["survey_date", "age", "sex", "income", "year_arrived_us"]
cv_cols_original = [
    "have you been diagnosed with any of the following  (choice=heart failure)",
    "have you been diagnosed with any of the following  (choice=hypertension)",
    "heart attack (choice=yes)",
    "stroke (choice=yes)"
]

all_needed_cols = [col for col in (core_cols + cv_cols_original) if col in df.columns]
df = df[all_needed_cols].copy()

print("✓ Column names cleaned and standardized")
print(f"✓ Variables selected: {len(df.columns)} variables retained")

# ==============================================================================
# STEP 3: Type Conversion & Outlier Removal
# ==============================================================================
df["survey_date"] = pd.to_datetime(df["survey_date"], errors="coerce")
df["age"] = pd.to_numeric(df["age"], errors="coerce")
df["year_arrived_us"] = pd.to_numeric(df["year_arrived_us"], errors="coerce")

print("\n⚡ OUTLIER DETECTION & REMOVAL")
print("-" * 60)

n_before = len(df)

# Age: 0-120
age_invalid = (df["age"] < 0) | (df["age"] > 120) | df["age"].isna()
n_age_invalid = age_invalid.sum()
print(f"Age < 0 or > 120: {n_age_invalid} records")

# Year arrived: 1900-2023
year_invalid = (df["year_arrived_us"] < 1900) | (df["year_arrived_us"] > 2023) | df["year_arrived_us"].isna()
n_year_invalid = year_invalid.sum()
print(f"Year arrived < 1900 or > 2023: {n_year_invalid} records")

# Keep records with valid age AND valid year
valid_mask = (~age_invalid) & (~year_invalid)
df = df[valid_mask].copy()

n_excluded_outliers = n_before - len(df)
print(f"\nTotal excluded: {n_excluded_outliers}")
print(f"Remaining: {len(df)}")

cohort_flow.append({
    'Stage': '2. Outliers removed',
    'N': len(df),
    'Excluded': n_excluded_outliers,
    'Reason': 'Invalid age or year of arrival'
})

# ==============================================================================
# STEP 4: Derived Variables
# ==============================================================================
df["arrival_date"] = pd.to_datetime(
    df["year_arrived_us"].astype("Int64").astype(str) + "-07-01",
    errors="coerce"
)
df["years_in_us"] = (df["survey_date"] - df["arrival_date"]).dt.days / 365.25
df.loc[(df["years_in_us"] < 0) | (df["years_in_us"] > 120), "years_in_us"] = np.nan

# Create bins
df["year_arrived_bin3"] = pd.cut(
    df["year_arrived_us"],
    bins=[0, 2005, 2015, 2025],
    labels=["Before 2005", "2005-2015", "2015-2023"],
    include_lowest=True
)

print("\n✓ Derived variables created (years_in_us, year_arrived_bin3)")

# ==============================================================================
# STEP 5: CV Outcome Processing
# ==============================================================================
cv_rename_map = {
    "have you been diagnosed with any of the following  (choice=heart failure)": "dx_hf",
    "have you been diagnosed with any of the following  (choice=hypertension)": "dx_htn",
    "heart attack (choice=yes)": "hx_mi",
    "stroke (choice=yes)": "hx_stroke",
}

df = df.rename(columns=cv_rename_map)

def to_binary(x):
    if pd.isna(x):
        return 0
    s = str(x).strip().lower()
    yes_set = {"yes", "y", "true", "1", "1.0", "checked", "check", "x", "selected"}
    no_set = {"no", "n", "false", "0", "0.0", "unchecked", "uncheck", ""}
    if s in yes_set:
        return 1
    if s in no_set:
        return 0
    if len(s) > 0:
        return 1
    return 0

cv_outcomes = ["dx_hf", "dx_htn", "hx_mi", "hx_stroke"]
for col in cv_outcomes:
    if col in df.columns:
        df[col] = df[col].apply(to_binary)

print("✓ CV outcomes converted to binary (0/1)")

# ==============================================================================
# STEP 6: Final Analysis Sample
# ==============================================================================
n_before_final = len(df)
df_analysis = df[df["year_arrived_bin3"].notna()].copy()
n_final = len(df_analysis)
n_excluded_final = n_before_final - n_final

print(f"\n🎯 FINAL ANALYSIS SAMPLE")
print("-" * 60)
print(f"Records before: {n_before_final}")
print(f"Records excluded: {n_excluded_final}")
print(f"Analysis sample: {n_final}")

cohort_flow.append({
    'Stage': '3. Final analysis sample',
    'N': n_final,
    'Excluded': n_excluded_final,
    'Reason': 'Missing year of arrival data'
})

# Create composite CV measures
cv_conditions = ["dx_hf", "dx_htn", "hx_mi", "hx_stroke"]
df_analysis["cv_burden_count"] = df_analysis[cv_conditions].sum(axis=1, skipna=True)
df_analysis["any_cv_condition"] = (df_analysis["cv_burden_count"] > 0).astype(int)
df_analysis["major_cv_event"] = ((df_analysis["hx_mi"] == 1) | (df_analysis["hx_stroke"] == 1)).astype(int)

# ==============================================================================
# COHORT FLOW SUMMARY
# ==============================================================================
cohort_flow_df = pd.DataFrame(cohort_flow)

print("\n" + "="*80)
print("COHORT FLOW SUMMARY")
print("="*80)

print(cohort_flow_df.to_string(index=False))

# ==============================================================================
# COHORT FLOW VISUALIZATION
# ==============================================================================
fig, ax = plt.subplots(figsize=(12, 6))

stages = cohort_flow_df['Stage'].tolist()
sample_sizes = cohort_flow_df['N'].tolist()
excluded = cohort_flow_df['Excluded'].tolist()

y_positions = np.arange(len(stages))[::-1]

colors = ['#2ecc71' if e == 0 else '#e74c3c' for e in excluded]
bars = ax.barh(y_positions, sample_sizes, color=colors, alpha=0.7, edgecolor='black', linewidth=2)

for i, (stage, n, ex) in enumerate(zip(stages, sample_sizes, excluded)):
    ax.text(n/2, len(stages)-1-i, f'N={int(n)}', 
            ha='center', va='center', fontweight='bold', fontsize=11, color='white')
    if ex > 0:
        ax.text(n + max(sample_sizes)*0.02, len(stages)-1-i, f'(-{int(ex)})', 
                ha='left', va='center', fontsize=10, color='#e74c3c', fontweight='bold')

ax.set_yticks(y_positions)
ax.set_yticklabels(stages, fontsize=11)
ax.set_xlabel('Sample Size (N)', fontsize=12, fontweight='bold')
ax.set_title('Phase 0 Cohort Flow: From Raw Data to Analysis Sample', fontsize=14, fontweight='bold', pad=20)
ax.set_xlim(0, max(sample_sizes) * 1.15)
ax.grid(axis='x', alpha=0.3)
ax.invert_yaxis()

plt.tight_layout()
plt.savefig('cohort_flow.png', dpi=300, bbox_inches='tight')
print("\n✓ Cohort flow visualization saved to: cohort_flow.png")

# ==============================================================================
# MISSING DATA ANALYSIS
# ==============================================================================
print("\n" + "="*80)
print("MISSING DATA ANALYSIS (Analysis Sample)")
print("="*80)

missing_summary = pd.DataFrame({
    'Variable': df_analysis.columns,
    'Missing_N': [df_analysis[col].isna().sum() for col in df_analysis.columns],
    'Missing_%': [df_analysis[col].isna().sum() / len(df_analysis) * 100 for col in df_analysis.columns],
    'Non_Missing_N': [df_analysis[col].notna().sum() for col in df_analysis.columns],
})

missing_summary = missing_summary.sort_values('Missing_%', ascending=False)

print(missing_summary.to_string(index=False))

# ==============================================================================
# DATA QUALITY SUMMARY
# ==============================================================================
print("\n" + "="*80)
print("DATA QUALITY SUMMARY")
print("="*80)

retention_pct = (n_final / n_initial) * 100

print(f"\n📊 SAMPLE RETENTION:")
print(f"   Raw sample: {n_initial}")
print(f"   Analysis sample: {n_final}")
print(f"   Retention rate: {retention_pct:.1f}%")
print(f"   Total excluded: {n_initial - n_final} ({100-retention_pct:.1f}%)")

print(f"\n📋 ANALYSIS SAMPLE CHARACTERISTICS:")
print(f"   Age, mean (SD): {df_analysis['age'].mean():.1f} ({df_analysis['age'].std():.1f})")
print(f"   Years in US, mean (SD): {df_analysis['years_in_us'].mean():.1f} ({df_analysis['years_in_us'].std():.1f})")

print(f"\n💓 CV OUTCOME PREVALENCE:")
print(f"   Hypertension: {df_analysis['dx_htn'].sum()} ({df_analysis['dx_htn'].mean()*100:.1f}%)")
print(f"   Heart attack: {df_analysis['hx_mi'].sum()} ({df_analysis['hx_mi'].mean()*100:.1f}%)")
print(f"   Stroke: {df_analysis['hx_stroke'].sum()} ({df_analysis['hx_stroke'].mean()*100:.1f}%)")
print(f"   Any CV condition: {df_analysis['any_cv_condition'].sum()} ({df_analysis['any_cv_condition'].mean()*100:.1f}%)")

print(f"\n📅 YEAR OF ARRIVAL DISTRIBUTION:")
for bin_name in df_analysis["year_arrived_bin3"].cat.categories:
    n_bin = (df_analysis["year_arrived_bin3"] == bin_name).sum()
    pct = n_bin / len(df_analysis) * 100
    print(f"   {bin_name}: {n_bin} ({pct:.1f}%)")

# Save for later use
df_analysis.to_csv('phase0_analysis_sample.csv', index=False)
print(f"\n✓ Analysis sample saved to: phase0_analysis_sample.csv")

print("\n" + "="*80)
print("✅ PHASE 0 DATA QUALITY AUDIT COMPLETE")
print("="*80)
