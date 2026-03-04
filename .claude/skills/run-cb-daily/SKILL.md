---
name: run-cb-daily
description: Process YouTrack criticality tickets and run the standard request workflow defined in experiments/crit_requests/WORKFLOW.md
argument-hint: "[ticket_id]"
---

# Skill: Run Crit-Buddy Daily

Process one or more YouTrack tickets through the standard criticality workflow.

## Source of Truth

`experiments/crit_requests/WORKFLOW.md` is authoritative for:
- config filenames
- run order
- manual handoffs between steps
- expected output paths
- final deliverables

If this skill conflicts with `WORKFLOW.md`, follow `WORKFLOW.md`.

## Usage

```text
/run-cb-daily
/run-cb-daily CB-10
```

## Workflow

### 1. Select tickets

- If a ticket ID is provided, fetch only that ticket:
  ```bash
  python -m critbuddy.integrations.youtrack.cli fetch {TICKET_ID} --json
  ```
- If no ticket ID is provided, fetch all tickets in Ready-for-run state:
  ```bash
  python -m critbuddy.integrations.youtrack.cli fetch-ready --json
  ```
- If no tickets are returned, report and stop.

### 2. Setup request directory (Phase 1 from `WORKFLOW.md`)

Create:

```text
experiments/crit_requests/{TICKET_ID}/
├── _config/
│   ├── 01_uf6_dry.yaml
│   ├── 02_hu_opt.yaml
│   ├── 03_wet_bottom_fill.yaml
│   └── 04_wet_torus_fill.yaml   # optional
├── runs/
└── results/
```

Generate config files from the ticket request and keep naming exactly as above.

Do not use legacy names such as:
- `uf6_dry.yaml`
- `uo2f2_hu_sweep.yaml`
- `uo2f2_fill_sweep.yaml`

Create `experiment-plan.md` from:
- `docs/templates/experiment-plan-template.md`

### 3. Mark ticket in progress

```bash
python -m critbuddy.integrations.youtrack.cli update-status {TICKET_ID} "In Progress"
python -m critbuddy.integrations.youtrack.cli comment {TICKET_ID} "Setup complete. Starting analysis workflow."
```

### 4. Execute analysis (Phase 2 from `WORKFLOW.md`)

Preferred command (recommended):

```bash
python -m critbuddy.analysis.orchestrator experiments/crit_requests/{TICKET_ID}
```

Manual equivalent:

```bash
python run_study.py experiments/crit_requests/{TICKET_ID}/_config/01_uf6_dry.yaml
python run_study.py experiments/crit_requests/{TICKET_ID}/_config/02_hu_opt.yaml
python run_study.py experiments/crit_requests/{TICKET_ID}/_config/03_wet_bottom_fill.yaml
# Optional
python run_study.py experiments/crit_requests/{TICKET_ID}/_config/04_wet_torus_fill.yaml
```

Manual handoffs must match `WORKFLOW.md`:

1. After `01_uf6_dry.yaml`:
- Read `runs/01_uf6_dry/latest/results.csv`
- Identify worst-case geometry (max k-eff)
- Update geometry in `02_hu_opt.yaml`

2. After `02_hu_opt.yaml`:
- Read `runs/02_hu_opt/latest/results.csv`
- Identify peak H/U (max k-eff)
- Update `03_wet_bottom_fill.yaml`
- Update `04_wet_torus_fill.yaml` (if used)

3. After `03_wet_bottom_fill.yaml`:
- Read `runs/03_wet_bottom_fill/latest/results.csv`
- Identify threshold where `k+2sigma >= 0.95`

4. After `04_wet_torus_fill.yaml` (optional):
- Compare bottom-fill vs torus-fill bounding behavior

### 5. Build final deliverables (Phase 3 from `WORKFLOW.md`)

Under `experiments/crit_requests/{TICKET_ID}/results/`, produce:
- `REPORT.md`
- `all_results.csv`
- `plots/*.png`

### 6. Publish back to YouTrack

```bash
python -m critbuddy.integrations.youtrack.cli push-results {TICKET_ID} experiments/crit_requests/{TICKET_ID}/results
python -m critbuddy.integrations.youtrack.cli mark-complete {TICKET_ID}
```

### 7. Failure handling

If setup, run, or publish fails:

```bash
python -m critbuddy.integrations.youtrack.cli mark-failed {TICKET_ID} "{ERROR_MESSAGE}"
```

## Safety Classification

Use the same thresholds as `WORKFLOW.md`:

| Status | Criterion |
|--------|-----------|
| SAFE | k+2sigma < 0.95 |
| MARGINAL | 0.95 <= k+2sigma < 1.00 |
| CRITICAL | k+2sigma >= 1.00 |
