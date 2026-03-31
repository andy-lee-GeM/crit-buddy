# Crit-Buddy Overview for Criticality Consultants

## Purpose

Crit-Buddy is an internal criticality analysis framework built to let any RE
run high-quality criticality studies without needing to hand-build every
transport model in MCNP.

The core idea is simple:

- a canonical physical model is implemented once in OpenMC
- the model is exposed through a config-driven interface
- an RE can then run parameter studies by editing a YAML config instead of
  editing transport code
- the resulting studies are traceable, reproducible, and easy to hand off to a
  certified criticality consultant for final MCNP implementation and licensing
  support

This removes a major bottleneck in the current workflow. Instead of waiting for
a specialist to build each exploratory case by hand, REs can evaluate design
space directly, identify promising and clearly subcritical concepts early, and
only escalate the final candidate designs for formal MCNP implementation and
licensed criticality submission.

## What Crit-Buddy Does

Crit-Buddy is not intended to replace the final certified MCNP workflow used
for regulatory or licensing submissions.

Its role is to:

- make criticality analysis accessible to non-specialist REs
- enable fast geometry and material sweeps from a config file
- provide a common reusable model library
- preserve traceability between model source, run configuration, exported
  cases, and comparison results
- create a structured handoff package for a certified criticality consultant

In practice, this means an RE can run studies such as:

- material substitutions
- dimension sweeps
- fill level sweeps
- boundary condition variations
- moderator changes
- enrichment and composition sensitivity cases

without rewriting the solver model each time.

## Why This Helps the Team

The main benefit is organizational leverage.

Without a tool like Crit-Buddy, every exploratory criticality question tends to
require direct consultant or specialist involvement. That is slow, expensive,
and difficult to scale across multiple concepts.

With Crit-Buddy:

- every RE can explore criticality behavior using a controlled model interface
- the team can eliminate non-viable designs earlier
- criticality consultants spend their time on final verification and
  licensing-grade deliverables rather than routine design-space exploration
- the final handoff is cleaner because the model logic, assumptions, material
  definitions, and parametric study history are already organized

This unblocks the entire RE team while still preserving the role of the
certified consultant in the final V&V and licensing path.

## How the Workflow Works

The workflow is intentionally staged.

### 1. Implement the canonical template model

A physical system is implemented as a reusable OpenMC model with a clean
parameter interface.

The goal is not to create a one-off study file. The goal is to create a
canonical model that can be driven from configuration.

### 2. Compare against the MCNP reference model

The OpenMC implementation is compared against the reference MCNP model,
typically based on the original Steven deck and Andy's cleaned implementation.

The acceptance goal is near-identical solver behavior, ideally on the order of
about `+/- 0.005 delta keff` for the certification cases. If a model does not
meet that target immediately, the remaining discrepancy is investigated and
documented.

### 3. Write a certification checkpoint

Once the OpenMC and MCNP models are sufficiently aligned, a certification
package is created.

Each certification preserves:

- the frozen OpenMC source snapshot
- the OpenMC study config
- deterministic exported OpenMC case files
- lightweight OpenMC results
- rerunnable MCNP inputs and outputs
- a short results summary documenting the comparison

This gives the team a stable checkpoint that can be rerun from a known git
commit.

### 4. Enable controlled exploration in OpenMC

After certification, the OpenMC model is set up for controlled parametric work.
This includes the ability to:

- substitute materials
- sweep dimensions
- change fills or boundary conditions
- vary enrichment, hydration, or other physically relevant parameters

This is the stage where REs can explore the design space quickly.

### 5. Perform the full criticality analysis

The RE uses the certified model as a design tool to evaluate options,
understand sensitivities, and identify configurations that are credibly
subcritical.

This is where most of the iteration happens, and this is the part of the
workflow that Crit-Buddy is designed to accelerate.

### 6. Handoff the final design for formal MCNP implementation

Once the RE has identified a criticality-safe design, the final result is
packaged for the certified consultant.

That package includes:

- the OpenMC model logic
- the geometry and material assumptions
- the reference certification results
- the material definitions used in the analysis
- the final chosen parameter set
- the supporting writeup

At that point, a certified criticality consultant can implement the final case
in MCNP on the validated environment, perform V&V in the required workflow, and
submit the NCSE/NRC-facing deliverable as needed for licensing.

## QA and Certification Philosophy

Crit-Buddy is useful only if the models are disciplined.

The QA philosophy is:

- one canonical model per physical problem
- one documented reference MCNP deck
- one frozen certification checkpoint per accepted baseline
- reproducible configs and exported cases
- explicit material definitions
- traceable git history from model code to study output

The certification process is deliberately lightweight, but it is not casual. It
is intended to create enough structure that a future engineer or consultant can
inspect what was done, rerun it, and understand why the baseline was accepted.

## Current Implemented Models

At present, two canonical models have been implemented and certified in this
workflow.

### 1. Centrifuge Unit Cell

This model represents a single cylindrical centrifuge vessel inside a
reflective square unit cell.

It includes:

- fuel region
- water film
- steel wall and end caps
- internal and external air regions
- config-driven fill-height sweeps

This model was especially useful for identifying and isolating a material
parity issue related to the air implementation. The current baseline preserves
the legacy MCNP air behavior through a dedicated `centrifuge_air` shared
material so the OpenMC certification baseline reproduces the intended MCNP
reference more closely.

### 2. Pipe Cross Model

This model represents reflected orthogonal pipe crossings for AD-7 parity work.

It supports:

- `xz` cross geometry
- `xyz` cross geometry
- UF6 gas cores
- annular UO2F2 fuel regions
- configurable wall material
- moderator and spacing sweeps

This model demonstrates the reusable config-driven workflow for a pipe-like
system and is useful for parametric exploration of crossing geometry and
separation effects.

## Shared Materials Library

A key part of Crit-Buddy is the shared materials library. This prevents each
model from redefining common materials differently and gives the team a single
place to inspect and reproduce material assumptions.

The current shared library includes these named static materials:

- `aluminum`
- `stainless_steel_304`
- `stainless_steel_316`
- `water`
- `concrete_ordinary`
- `air_dry`
- `humid_air`
- `centrifuge_air`
- `void`
- `vacuum`

In addition to those static materials, the framework also builds generated
fissile/process materials such as:

- `uf6`
- `uo2f2`

These are important because they are not just hard-coded compositions. They are
parameterized materials tied to enrichment, density, and hydration assumptions,
which makes them appropriate for controlled sweeps.

For consultant handoff, the material package should include:

- the named library materials
- the generated `UF6` and `UO2F2` definitions used in the final study
- densities and composition assumptions
- any special-case certification materials such as `centrifuge_air`

## What the Consultant Should Understand

The most important point is this:

Crit-Buddy is an engineering productivity and traceability tool, not a
replacement for final licensed MCNP work.

It allows the RE team to do the heavy exploratory work up front:

- identify safe regions
- understand sensitivities
- converge on viable designs
- preserve model history and assumptions

Then the certified consultant can focus on the high-value final task:

- implement the accepted design in MCNP
- perform final V&V in the qualified environment
- prepare the formal NCSE/licensing submission

This is the correct division of labor. It gives the RE team speed without
weakening the rigor of the final consultant-delivered product.

## Recommended Consultant Handoff Package

For each final concept, the handoff package should contain:

- the canonical OpenMC `model.py`
- the config file used for the accepted design
- the certification checkpoint used as the baseline
- exported OpenMC case files
- the shared material library definitions
- the generated final material cards for the accepted design
- a short model assumptions document
- the study summary showing how the design space was explored
- the final selected geometry and material parameters

That package gives the consultant everything needed to reproduce the
engineering intent and translate it into the final validated MCNP workflow.

## Summary

Crit-Buddy exists to make criticality analysis scalable across the RE team.

It does this by:

- turning transport models into reusable config-driven tools
- validating those tools against reference MCNP cases
- preserving certification checkpoints for traceability
- enabling rapid design-space exploration in OpenMC
- handing off the final accepted design to certified consultants for MCNP V&V
  and licensing submission

The result is faster engineering iteration, better traceability, and more
efficient use of specialized criticality consulting effort.
