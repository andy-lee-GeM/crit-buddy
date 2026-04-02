# Standard Report Format

Keep `requests/{REQUEST_ID}/results/REPORT.md` lightweight.

Preferred plotting flow:

```bash
python -m critbuddy.reporting.plots keff requests/{REQUEST_ID}/runs/03_wet_bottom_fill/latest/results.csv --x fill_fraction_percent --title "UO2F2 Wet Bottom Fill Threshold" --output requests/{REQUEST_ID}/results/plots/03_wet_bottom_fill_keff_vs_fill_fraction_percent.png
```

That CLI only generates one diagram from one `results.csv`. The skill is
responsible for request-directory conventions, plot selection, and final report
assembly.

It only needs these sections:

## 1. Title

Use:

`# {REQUEST_ID}: {equipment or request title} - Criticality Analysis`

## 2. Main Takeaways

Use 3-5 bullets covering the key outcome, for example:

- controlling case
- peak moderation point
- critical threshold
- safe operating limit, if one exists
- maximum observed reactivity

## 3. Tables of k-eff

Include compact tables for the standard three analyses.

### Step 1: UF6 Dry

| Fill Height or Geometry Parameter | k-eff + 2σ | Status |
|-----------------------------------|------------|--------|

### Step 2: H/U Optimization

| H/U Ratio | k-eff + 2σ | Status |
|-----------|------------|--------|

### Step 3: Wet UO2F2 Threshold

| Fill Height or Fill Fraction | k-eff + 2σ | Status |
|------------------------------|------------|--------|

## 4. Visualizations

Include the decision-useful plots for the three analyses.

Always generate exactly these three titled line graphs:

- `UF6 Dry Screening`
- `H/U Optimization`
- `UO2F2 Wet Bottom Fill Threshold`

Recommended filenames:

- `01_uf6_dry_keff_vs_fill_fraction_percent.png`
- `02_hu_opt_keff_vs_h_to_u.png`
- `03_wet_bottom_fill_keff_vs_fill_fraction_percent.png`

Embed these visuals in `REPORT.md` using markdown image references:

- `![UF6 Dry Screening](plots/01_uf6_dry_keff_vs_fill_fraction_percent.png)`
- `![H/U Optimization](plots/02_hu_opt_keff_vs_h_to_u.png)`
- `![UO2F2 Wet Bottom Fill Threshold](plots/03_wet_bottom_fill_keff_vs_fill_fraction_percent.png)`

This is required so YouTrack comments can render the attached visuals inline
when `push-results` publishes the report.

Optional additions:

- add up to 2 extra plots if they materially improve the decision readout
- common examples:
  - geometry or status plot when it clarifies the controlling case

Guidance:

- `results/plots/` should contain the curated report artifacts, not every plot
  generated under the run directories
- avoid duplicate line plots that show the same trend with only axis inversion
