---
name: run-criticality-request
description: Run the standard crit-buddy 3-step criticality request workflow for a user request or YouTrack ticket
argument-hint: "[ticket_id or request]"
---

# Skill: Run Criticality Request

Run the standard crit-buddy 3-step request workflow for either:

- a YouTrack ticket such as `CB-14`
- a direct user request with no ticket yet

The job is to:

1. create a standard request workspace
2. create the three standard configs
3. create `experiment-plan.md`
4. run the three analyses in order
5. update downstream configs between steps
6. build the final result package
7. update YouTrack if a ticket exists

Use recent requests such as CB-13 and CB-14 as the behavioral model.

## Core Workflow

The standard three analyses are:

1. `01_uf6_dry.yaml`
Purpose: identify the worst-case dry geometry or fill condition.

2. `02_hu_opt.yaml`
Purpose: identify the peak `h_to_u` at the worst-case geometry.

3. `03_wet_bottom_fill.yaml`
Purpose: identify the wet UO2F2 threshold at the peak moderation from step 2.

Use the numbered config filenames above as the canonical local config names.

## Inputs

If a ticket ID is provided:

- fetch the ticket with:
  ```bash
  python -m critbuddy.integrations.youtrack.cli fetch {TICKET_ID} --json
  ```
- use the ticket fields and description to build the request

If no ticket ID is provided:

- use the user request directly
- choose a concise request ID for the local workspace
- skip YouTrack update steps unless the user later provides a ticket

## Request Workspace

Create a request workspace under:

```text
requests/{REQUEST_ID}/
├── configs/
│   ├── 01_uf6_dry.yaml
│   ├── 02_hu_opt.yaml
│   └── 03_wet_bottom_fill.yaml
├── runs/
├── results/
└── experiment-plan.md
```

Notes:

- If a YouTrack ticket exists, `{REQUEST_ID}` should normally be the ticket ID, for example `CB-14`.
- `02_hu_opt.yaml` should start with placeholder geometry that will be replaced after step 1.
- `03_wet_bottom_fill.yaml` should start with placeholder geometry and placeholder `h_to_u` that will be replaced after step 2.
- Always create `experiment-plan.md` in the request directory before running studies.

## Experiment Plan

Create:

```text
requests/{REQUEST_ID}/experiment-plan.md
```

This file should explain exactly what will be run in this request directory and in what order.

At minimum, it should include:

- request objective and summary
- request ID and ticket ID if one exists
- the three config files in `configs/`
- the exact run sequence for steps 1, 2, and 3
- the handoff after step 1
- the handoff after step 2
- success criteria
- expected artifacts under `results/`

Treat `experiment-plan.md` as the operator checklist for the request.

## Standard Execution

Run the three studies in order:

```bash
python run_study.py requests/{REQUEST_ID}/configs/01_uf6_dry.yaml
python run_study.py requests/{REQUEST_ID}/configs/02_hu_opt.yaml
python run_study.py requests/{REQUEST_ID}/configs/03_wet_bottom_fill.yaml
```

Do not treat this as a blind batch run. The downstream configs must be updated between steps.

## Manual Handoffs

### After `01_uf6_dry.yaml`

- Read `requests/{REQUEST_ID}/runs/01_uf6_dry/latest/results.csv`
- Identify the worst-case geometry or fill condition using the highest `keff + 2sigma`
- Update the geometry inputs in `02_hu_opt.yaml`

### After `02_hu_opt.yaml`

- Read `requests/{REQUEST_ID}/runs/02_hu_opt/latest/results.csv`
- Identify the peak `h_to_u` using the highest `keff + 2sigma`
- Update `03_wet_bottom_fill.yaml` with the selected geometry and `h_to_u`

### After `03_wet_bottom_fill.yaml`

- Read `requests/{REQUEST_ID}/runs/03_wet_bottom_fill/latest/results.csv`
- Identify where `keff + 2sigma` crosses or approaches the administrative limit
- Determine the controlling wet-fill criticality condition

## Results Package

After the three analyses are complete, build the final package under:

```text
requests/{REQUEST_ID}/results/
```

Required artifacts:

- `REPORT.md`
- `all_results.csv`
- `plots/*.png`

Use the standard report format in:

- `references/report-format.md`

The plotting CLI is intentionally narrow. It should only generate a single
diagram from a single `results.csv`. The skill owns request-directory
conventions, plot curation, file copying, and report assembly.

Always generate these three titled line graphs for the final request package:

- `UF6 Dry Screening`
- `H/U Optimization`
- `UO2F2 Wet Bottom Fill Threshold`

Recommended commands:

```bash
python -m critbuddy.reporting.plots keff requests/{REQUEST_ID}/runs/01_uf6_dry/latest/results.csv --x fill_fraction_percent --title "UF6 Dry Screening" --output requests/{REQUEST_ID}/results/plots/01_uf6_dry_keff_vs_fill_fraction_percent.png
python -m critbuddy.reporting.plots keff requests/{REQUEST_ID}/runs/02_hu_opt/latest/results.csv --x h_to_u --title "H/U Optimization" --output requests/{REQUEST_ID}/results/plots/02_hu_opt_keff_vs_h_to_u.png
python -m critbuddy.reporting.plots keff requests/{REQUEST_ID}/runs/03_wet_bottom_fill/latest/results.csv --x fill_fraction_percent --title "UO2F2 Wet Bottom Fill Threshold" --output requests/{REQUEST_ID}/results/plots/03_wet_bottom_fill_keff_vs_fill_fraction_percent.png
```

### Plot Curation

Do not treat `results/plots/` as a dump of every generated plot.

Curate the final reporting directory so it contains the selected report-facing
artifacts only:

- the required `UF6 Dry Screening` line plot
- the required `H/U Optimization` line plot
- the required `UO2F2 Wet Bottom Fill Threshold` line plot
- optionally 1-2 additional plots if they materially improve the engineering
  readout

Good optional additions include:

- one geometry or status plot when it materially clarifies the controlling case

Avoid copying low-signal duplicates into `results/plots/` just because the run
directory produced them.

Embed the three required visuals in `REPORT.md` using markdown image references
to `plots/{filename}.png`. This is required so the YouTrack publish step can
render the visuals directly in the ticket comment.

## Ticket Publishing

If a ticket exists, update it through the workflow.

When setup is complete:

```bash
python -m critbuddy.integrations.youtrack.cli update-status {TICKET_ID} "In Progress"
python -m critbuddy.integrations.youtrack.cli comment {TICKET_ID} "Setup complete. Starting standard 3-step criticality workflow."
```

When results are ready:

```bash
python -m critbuddy.integrations.youtrack.cli push-results {TICKET_ID} requests/{REQUEST_ID}/results
python -m critbuddy.integrations.youtrack.cli mark-complete {TICKET_ID}
```

The ticket publish step should push:

- the final `REPORT.md` content as a ticket comment
- `all_results.csv` as an attachment
- the curated PNG plots under `results/plots/` as attachments

The ticket comment should embed the required visuals, not just list them as
attachments. The expected path is:

- include `![...](plots/01_uf6_dry_keff_vs_fill_fraction_percent.png)` in `REPORT.md`
- include `![...](plots/02_hu_opt_keff_vs_h_to_u.png)` in `REPORT.md`
- include `![...](plots/03_wet_bottom_fill_keff_vs_fill_fraction_percent.png)` in `REPORT.md`

`python -m critbuddy.integrations.youtrack.cli push-results ...` rewrites those
`plots/...` references to attachment-backed image embeds in the posted comment.

If there is no ticket, skip these steps and return the local result package to the user.

## Failure Handling

If a ticket exists and setup, run, or publishing fails:

```bash
python -m critbuddy.integrations.youtrack.cli mark-failed {TICKET_ID} "{ERROR_MESSAGE}"
```

If there is no ticket, report the failure clearly and preserve the local request directory for debugging.

## Safety Classification

Use the standard administrative thresholds:

| Status | Criterion |
|--------|-----------|
| SAFE | `keff + 2sigma < 0.95` |
| MARGINAL | `0.95 <= keff + 2sigma < 1.00` |
| CRITICAL | `keff + 2sigma >= 1.00` |
