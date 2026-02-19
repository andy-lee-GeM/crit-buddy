# Experiment Plan: CB-8

## Ticket Information

- **Ticket ID**: CB-8
- **Title**: Parallel Pipe Sweep and Sensitivity Curves
- **Template**: `pipe`
- **Enrichment**: 75-100 wt% U-235 (sensitivity sweep)

---

## Configuration

| Parameter | Value | Notes |
|-----------|-------|-------|
| enrichment | [75, 85, 95, 100] | Swept for sensitivity curves |
| rows | [1, 2, 3, 4, 5, 6] | Swept |
| cols | [1, 2, 3, 4, 5, 6] | Swept |
| gap_cm | [0, 10, 20, 30, 40, 50] | Swept |
| pipe_size | [3, 4, 6] | Swept (NPS) |
| length_cm | 1000 | Fixed |
| wall_material | aluminum | From ticket |

---

## 3-Step Safety Case

### Step 1: UF6 Dry (Geometry + Enrichment Sweep)

**Config**: `_config/uf6_dry.yaml`

| Parameter | Values | Cases |
|-----------|--------|-------|
| enrichment | [75, 85, 95, 100] | 4 |
| rows | [1, 2, 3, 4, 5, 6] | 6 |
| cols | [1, 2, 3, 4, 5, 6] | 6 |
| gap_cm | [0, 10, 20, 30, 40, 50] | 6 |
| pipe_size | [3, 4, 6] | 3 |

**Total cases**: 4 x 6 x 6 x 6 x 3 = **2,592 cases**

**WARNING**: This is a large sweep. Consider reducing parameters if runtime is a concern.

**Goal**: Find worst-case geometry and enrichment (highest k-eff)

### Step 2: H/U Sweep (at worst-case geometry)

**Config**: `_config/uo2f2_hu_sweep.yaml`

| Parameter | Values | Cases |
|-----------|--------|-------|
| h_to_u | [0, 10, 20, 30, 40, 50] | 6 |

**Total cases**: **6 cases**

**Goal**: Find peak H/U ratio (optimal moderation)

### Step 3: Fill Sweep (at worst-case + peak H/U)

**Config**: `_config/uo2f2_fill_sweep.yaml`

| Parameter | Values | Cases |
|-----------|--------|-------|
| fill_fraction | [0.1, 0.2, ..., 1.0] | 10 |

**Total cases**: **10 cases**

**Goal**: Find critical threshold (fill % where k-eff + 2σ ≥ 0.95)

---

## Total Simulation Cases

| Step | Config | Cases |
|------|--------|-------|
| 1 | uf6_dry.yaml | 2,592 |
| 2 | uo2f2_hu_sweep.yaml | 6 |
| 3 | uo2f2_fill_sweep.yaml | 10 |
| **Total** | | **2,608 cases** |

---

## Runtime Estimate

At ~2 minutes per case (smoke test) or ~10 minutes per case (full run):
- Smoke test: ~87 hours
- Full run: ~435 hours (18 days)

**Recommendation**: Consider reducing sweep granularity or running in parallel.

---

## Commands

```bash
# Step 1: UF6 Dry (WARNING: 2,592 cases)
python run_study.py experiments/crit_requests/CB-8/_config/uf6_dry.yaml

# After Step 1: Update uo2f2_hu_sweep.yaml and uo2f2_fill_sweep.yaml with worst-case geometry

# Step 2: H/U Sweep
python run_study.py experiments/crit_requests/CB-8/_config/uo2f2_hu_sweep.yaml

# After Step 2: Update uo2f2_fill_sweep.yaml with peak H/U

# Step 3: Fill Sweep
python run_study.py experiments/crit_requests/CB-8/_config/uo2f2_fill_sweep.yaml
```

---

## Success Criteria

- [ ] All cases complete without errors
- [ ] Worst-case geometry identified from Step 1
- [ ] Peak H/U ratio identified from Step 2
- [ ] Critical threshold identified from Step 3
- [ ] Safety classification determined (SAFE/MARGINAL/CRITICAL)
- [ ] Sensitivity curves generated for enrichment vs k-eff
