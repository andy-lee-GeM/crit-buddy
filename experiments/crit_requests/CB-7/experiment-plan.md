# Experiment Plan: CB-7

## Ticket Information

- **Ticket ID**: CB-7
- **Title**: GMPEF Phase 1 Mobile Rig Chemical Trap Array
- **Template**: `cylinder`
- **Enrichment**: 20 wt% U-235

---

## Configuration

| Parameter | Value | Notes |
|-----------|-------|-------|
| rows | [1, 5, 10] | Swept |
| cols | 10 | Fixed |
| layers | 1 | Fixed |
| gap_horizontal_cm | [0, 2.54, 10.16] | Swept |
| gap_vertical_cm | 0 | Fixed |
| radius_cm | 7.62 | Fixed |
| height_cm | 121.92 | Fixed |
| wall_material | steel | From ticket |
| wall_thickness_cm | 0.3175 | From ticket |

---

## 3-Step Safety Case

### Step 1: UF6 Dry (Geometry Sweep)

**Config**: `_config/uf6_dry.yaml`

| Parameter | Values | Cases |
|-----------|--------|-------|
| rows | [1, 5, 10] | 3 |
| gap_horizontal_cm | [0, 2.54, 10.16] | 3 |

**Total cases**: 3 x 3 = **9 cases**

**Goal**: Find worst-case geometry (highest k-eff)

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
| 1 | uf6_dry.yaml | 9 |
| 2 | uo2f2_hu_sweep.yaml | 6 |
| 3 | uo2f2_fill_sweep.yaml | 10 |
| **Total** | | **25 cases** |

---

## Commands

```bash
# Step 1: UF6 Dry
python run_study.py experiments/crit_requests/CB-7/_config/uf6_dry.yaml

# After Step 1: Update uo2f2_hu_sweep.yaml and uo2f2_fill_sweep.yaml with worst-case geometry

# Step 2: H/U Sweep
python run_study.py experiments/crit_requests/CB-7/_config/uo2f2_hu_sweep.yaml

# After Step 2: Update uo2f2_fill_sweep.yaml with peak H/U

# Step 3: Fill Sweep
python run_study.py experiments/crit_requests/CB-7/_config/uo2f2_fill_sweep.yaml
```

---

## Success Criteria

- [ ] All 25 cases complete without errors
- [ ] Worst-case geometry identified from Step 1
- [ ] Peak H/U ratio identified from Step 2
- [ ] Critical threshold identified from Step 3
- [ ] Safety classification determined (SAFE/MARGINAL/CRITICAL)
