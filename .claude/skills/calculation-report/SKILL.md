---
name: calculation-report
description: Generate a formal criticality safety calculation report from experiment results
argument-hint: "[experiment_directory]"
---

# Skill: Generate Calculation Report

Transform completed experiment results into a formal calculation document following the standard template structure. This creates documentation suitable for regulatory review and team communication.

## Usage

```
/calculation-report [experiment_directory]
```

If no path is provided, list available experiments with completed runs.

Examples:
```
/calculation-report
/calculation-report experiments/crit_requests/06_cylinder_array_3d
```

## Instructions

### If no experiment path is provided:

1. Use Glob to find directories containing `runs/*/results.csv`
2. List experiments that have completed runs
3. Use AskUserQuestion to let the user select which experiment to document
4. Proceed with report generation

### If experiment path is provided:

Generate the formal calculation report following these steps:

### 1. LOCATE RUN DATA

Find completed experiment runs:
```
{experiment_dir}/runs/{run_name}/{timestamp}/results.csv
```

Look for multiple conditions (e.g., optimal moderation + flooded) by checking for multiple run directories.

Use the `latest` symlink if available, otherwise use the most recent timestamp.

### 2. ANALYZE RESULTS

Read each `results.csv` and extract:
- **Swept parameters**: Columns with multiple unique values
- **Fixed parameters**: Columns with single values
- **k-eff range**: Min and max values
- **Safety status counts**: SAFE, MARGINAL, CRITICAL
- **Limiting condition**: Which condition has highest k-eff values

Identify the water density for each condition to label them properly:
- 0.5 g/cc = "Worst-Case Moderation"
- 1.0 g/cc = "Flooded"

### 3. GENERATE REPORT

Use the report generator:

```python
import sys
sys.path.insert(0, '/mnt/c/Users/AndyLee/Projects/crit-buddy')

from critbuddy.reporting import generate_calculation_report

run_dirs = {
    'optimal_moderation': '{path_to_0.5_run}',
    'flooded': '{path_to_1.0_run}',
}

generate_calculation_report(
    run_dirs=run_dirs,
    output_path='{experiment_dir}/{NAME}_CALCULATION.md',
    experiment_name='Descriptive Name',
)
```

### 4. GENERATE WORD DOCUMENT

Convert to formatted docx:

```python
from critbuddy.reporting.docx_generator import generate_calculation_docx

generate_calculation_docx(
    markdown_path='{experiment_dir}/{NAME}_CALCULATION.md',
    output_path='{experiment_dir}/{NAME}_CALCULATION.docx',
)
```

### 5. VERIFY OUTPUTS

Check that the following were generated:
- `{NAME}_CALCULATION.md` - Markdown report
- `{NAME}_CALCULATION.docx` - Word document
- `plots/geometry.png` - Geometry visualization
- `plots/keff_vs_gap_*.png` - Line plots for each condition
- `plots/heatmap_*.png` - Heatmaps for each condition

### 6. PRESENT SUMMARY

Display to the user:

1. **Report location**: Full path to generated files
2. **Key findings table**: Minimum safe values by enrichment
3. **Condition comparison**: Show Δk between worst-case and flooded
4. **Any warnings**: Missing data, unexpected results, etc.

Example summary:
```
## Calculation Report Generated

**Files created:**
- CASCADE_ARRAY_CALCULATION.md
- CASCADE_ARRAY_CALCULATION.docx

**Key Findings (Worst-Case Moderation):**

| Enrichment | Minimum Safe Gap | k-eff | Status |
|------------|------------------|-------|--------|
| 5%         | 7.62 cm          | 0.891 | SAFE   |
| 10%        | 10.0 cm          | 0.906 | SAFE   |
| 15-24%     | 20.0 cm          | 0.70-0.76 | SAFE |

Worst-case moderation (0.5 g/cc) produces Δk = +0.23 to +0.27
compared to fully flooded conditions.
```

---

## Report Structure

The generated report includes these sections:

### 1. References
- ANSI/ANS-8.1-2014, 10 CFR 70.24, NUREG/CR-6698
- OpenMC and ENDF/B-VIII.0 references

### 2. Purpose
Narrative paragraphs explaining:
- What question the analysis answers
- Configuration being analyzed (e.g., 10×5×4 = 200 cylinders)
- Parameter ranges studied
- Why both moderation conditions are evaluated

### 3. Inputs
- **3.1 Geometry Visualization**: XY cross-section image
- **3.2 Array Configuration**: Rows, columns, layers table
- **3.3 Cylinder Geometry**: Dimensions table
- **3.4 Materials**: With note that water serves as both moderator AND reflector
- **3.5 Parameter Ranges**: Enrichment, gap, water density values

### 4. Assumptions
- Optimal moderation explanation (why 0.5 g/cc is worst-case)
- Conservative assumptions table with justifications
- Non-conservative aspects acknowledged

### 5. Analytical Methods
- Monte Carlo code and nuclear data
- Simulation parameters (particles, batches)
- Geometry model description
- Statistical uncertainty treatment (k-eff + 2σ)

### 6. Results
For each condition:
- **6.1 Worst-Case Moderation (0.5 g/cc)**: Explanation + table + plots
- **6.2 Flooded (1.0 g/cc)**: Explanation + table + plots

Each includes:
- Brief explanation of what the condition represents
- k-effective table (enrichment × gap)
- Line plot (k-eff vs gap by enrichment)
- Heatmap visualization

### 7. Conclusions
- Minimum safe gap table by enrichment
- Key findings in narrative form

### 8. Attachments
- References to geometry plots, CSV files, configuration files

---

## Key Terminology

Use these standard terms in the report:

| Term | Meaning |
|------|---------|
| Worst-Case Moderation | Water density (~0.5 g/cc) producing peak reactivity |
| Flooded | Full water density (1.0 g/cc) |
| SAFE | k-eff + 2σ < 0.95 |
| MARGINAL | 0.95 ≤ k-eff + 2σ < 1.0 |
| CRITICAL | k-eff + 2σ ≥ 1.0 |
| Moderator | Water between fissile units (thermalizes neutrons) |
| Reflector | Water surrounding the array (returns neutrons) |

---

## Important Notes

- Always explain WHY worst-case moderation (0.5 g/cc) is more reactive than flooded
- Include geometry visualization so reviewers understand the setup
- Clarify that water serves as BOTH moderator (between units) AND reflector (around array)
- State minimum safe values clearly in the conclusions
- The solid UF6 density (5.09 g/cc) bounds accident scenarios (solidification, condensation)
