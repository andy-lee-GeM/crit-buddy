---
name: review-experiment
description: Review a criticality experiment before approval with a comprehensive checklist for verification
argument-hint: "[experiment_yaml_path]"
---

# Skill: Review Experiment

Review a criticality experiment before approval. This skill provides a comprehensive checklist for code reviewers to verify an experiment is correctly configured and ready to run.

## Usage

```
/review-experiment [experiment_yaml_path]
```

If no path is provided, list available experiments and let the user choose.

Example:
```
/review-experiment
/review-experiment experiments/crit_requests/01_single_cylinder/enr_24/radius_height.yaml
```

## Instructions

### If no experiment path is provided:

1. Use Glob to find all YAML files in `experiments/crit_requests/**/*.yaml`
2. Group them by directory (e.g., `00_moderation/`, `01_single_cylinder/enr_20/`, etc.)
3. Display them in a numbered list organized by category
4. Use AskUserQuestion to let the user select which experiment to review
5. Then proceed with the full review below

### If experiment path is provided:

Perform a thorough experiment review covering ALL sections below. Present the review in a structured format that a code reviewer can approve or reject.

### 1. EXPERIMENT OVERVIEW

Read the YAML file and summarize:
- **Experiment Name**: From the `name` field
- **Problem Template**: Which template is being used
- **Purpose**: What question does this experiment answer?
- **Equipment Coverage**: What physical equipment/scenarios does this cover?
- **Criticality Request Reference**: Link to the original request if known

### 2. PARAMETER CONFIGURATION

Display the full YAML file contents, then analyze:
- **Swept Parameters**: Which parameters are being varied? Show ranges.
- **Fixed Parameters**: Which parameters are held constant? Justify why.
- **Case Count**: Calculate total number of cases (cartesian product of sweeps)
- **Water Density**: What water density is used for moderation? (optimal is ~0.5 g/cc)

### 3. GEOMETRY VISUALIZATION

Show the geometry validation images:
- Display the 2D geometry plot (`_validation/geometry.png`)
- Display the 3D voxel plot (`_validation/voxel_3d.png`)
- If images don't exist, offer to generate them with `--validate` and `--voxel`

Verify visually:
- Materials are correctly colored and positioned
- Reflector surrounds the geometry appropriately
- No unexpected voids or overlaps

### 4. MODEL IMPLEMENTATION REVIEW

Read and display the OpenMC model file (`openmc/model.py` in the template directory).

Verify:
- **Materials**: Correct material functions used (e.g., `create_uf6` for pure UF6)
- **Geometry**: Surfaces and cells correctly define the problem
- **Boundary Conditions**: Reflective or vacuum as appropriate
- **Source**: Initial source distribution is reasonable

Show a sample of the derived parameters by running a quick validation.

### 5. CONSERVATIVE ASSUMPTIONS CHECK

Verify the experiment uses bounding assumptions:

| Assumption | Setting | Conservative? |
|------------|---------|---------------|
| Enrichment | [value] | Highest credible? |
| UF6 Density | [value] | Solid density (5.09 g/cc)? |
| Water Density | [value] | Optimal moderation (~0.5 g/cc)? |
| Reflection | [material] | Full water reflection (30 cm)? |
| Fill level | [value] | 100% fill assumed? |
| Wall material | [value] | Low absorption (aluminum)? |
| Temperature | Room temp | Most reactive? |

### 6. SIMULATION QUALITY

From the template's SIMULATION settings:
- **Particles per batch**: [value]
- **Total batches**: [value]
- **Inactive batches**: [value]
- **Expected uncertainty**: ~[estimate] pcm (based on particle count)

Is this sufficient for the safety determination?

### 7. SAFETY CRITERIA

- **Safety Limit**: k-eff + 2σ < [limit] (typically 0.95)
- **Classification**: SAFE / MARGINAL / CRITICAL thresholds
- **Regulatory Basis**: ANSI/ANS-8.1, 10 CFR 70.24, etc.

### 8. EXPECTED OUTPUTS

What will this experiment produce?
- Results CSV with k-eff values
- Plots (line graph, heatmap, etc.)
- Subcritical limits at each enrichment

### 9. APPROVAL CHECKLIST

Present a final checklist:

```
[ ] Geometry visualizations look correct
[ ] Materials are properly defined (pure UF6 at 5.09 g/cc)
[ ] Parameter ranges are appropriate
[ ] Water density at optimal moderation (~0.5 g/cc, conservative)
[ ] Full water reflection assumed (30 cm, conservative)
[ ] Simulation statistics are adequate
[ ] Safety limit is clearly defined
[ ] Experiment answers the intended question
```

### 10. RECOMMENDATION

Based on the review, provide one of:
- **APPROVED**: Ready to run
- **APPROVED WITH COMMENTS**: Minor issues noted but acceptable
- **CHANGES REQUESTED**: Specific changes needed before approval
- **REJECTED**: Fundamental issues that need redesign

---

## Notes

- Always use absolute paths when running commands
- Use the Read tool to display file contents
- Use the Read tool to display PNG images (Claude can view images)
- Be thorough - this is a safety-critical review
