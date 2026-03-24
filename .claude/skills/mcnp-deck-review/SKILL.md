---
name: mcnp-deck-review
description: Explain, review, and sanity-check an MCNP deck with emphasis on geometry intuition. Use when the user wants a high-level walkthrough of an MCNP model, help interpreting cell and surface cards, or a fast way to verify reflected boxes, cylinders, and region definitions.
argument-hint: "[path-to-deck]"
---

# MCNP Deck Review

## Overview
Use this skill when the user needs to understand an MCNP input, especially the geometry. The goal is not to repeat the deck line by line in raw syntax. The goal is to turn the deck into a small set of synchronized views that make the geometry easy to verify quickly.

Default to this structure:
1. What the model represents physically
2. Surface legend
3. ASCII plane views
4. Cell recipes in plain English
5. Geometry invariants
6. Raw line references for spot checks

Lead with intuition, then show the formal mapping.

## Core Principle
Do not force the reader to bounce back and forth between surface cards and cell cards. Translate the deck into a compact geometry system first, then explain how the cells fill that system.

Use a combination of:
- short narrative
- compact tables
- ASCII sketches
- MCNP line references
- verification checklists

## Workflow

### 1. Start High-Level
Before discussing syntax, state:
- what equipment or physical arrangement is being modeled
- whether the model is linear, crossed, arrayed, reflected, vacuum-bounded, or finite
- what the main material regions are
- what the repeating unit cell or bounding region is

Keep this to one short paragraph plus 3-5 bullets.

### 2. Build A Surface Legend
Make one compact table that defines every geometry-driving surface. Group surfaces by role.

Recommended columns:
- `Surface`
- `MCNP`
- `Meaning`
- `Intuition`

Example roles:
- z-directed pipe surfaces
- x-directed pipe surfaces
- outer reflective planes
- fill-height planes
- source or tally reference planes if relevant

Always explain the sign rule once:

```text
-surface = inside / negative side
+surface = outside / positive side
```

For annuli, explicitly decode patterns like:

```text
11 -2  => outside 11, inside 2
2 -1   => outside 2, inside 1
```

### 3. Draw Only The Plane Views That Matter
Use ASCII to show the smallest number of views that explains the geometry.

Preferred pattern:
- one view showing where axes/centers lie
- one view showing radial nesting or offsets

For crossed cylinders, `y-z` is usually the most informative view.
For vertical cylinders in a box, `x-y` plus `x-z` is usually enough.

ASCII diagrams should:
- label axes
- label centers
- show relative offsets
- show radial nesting as gas -> fuel -> wall
- show reflective or vacuum box limits when they matter

Do not try to render the full 3D model in one ASCII figure.

### 4. Rewrite Cells As Recipes
Do not start with raw cell cards. First write each cell as a plain-English region recipe.

Recommended columns:
- `Cell`
- `Material`
- `Plain-English Region`
- `MCNP`

Translate each cell into language like:
- inside z-pipe gas core
- outside gas core, inside fuel outer radius
- inside reflected box, outside both outer pipe surfaces

Use this grammar:
- `inside <surface>`
- `outside <surface>`
- `between <plane A> and <plane B>`
- `inside box, outside all solid regions`

Only after the plain-English recipe should you show the original MCNP terms.

### 5. Add Nesting Chains
Whenever a model has concentric regions, add a one-line nesting summary. This is often the fastest verification aid.

Example:

```text
z-pipe radial nesting:
11 -> 2 -> 1
gas -> fuel -> wall
```

Do the same for every repeated region family.

### 6. End With Geometry Invariants
Provide a short checklist of facts that must be true if the geometry was interpreted correctly.

Examples:
- pipe centerline is at the origin
- offset axis is at `y = 11.43 cm`
- outer-wall gap is `pitch - 2r`
- all six outer planes are reflective
- water fills the box minus both pipe outer volumes
- material `m4` is defined but unused

This should be short and scannable. The user should be able to verify the model from this checklist alone.

## Recommended Output Format

Use this section order unless the user asks for something narrower:

### 1. Model Summary
- one paragraph
- short bullets for main physical facts

### 2. Surface Legend
- compact table

### 3. Geometry Views
- 1-2 ASCII diagrams

### 4. Cell Recipes
- compact table

### 5. Invariants
- short checklist

### 6. Source References
- file references with line numbers for the most important surfaces and cells

## Interpretation Rules

### Cylinders
When interpreting cylinder cards, always state the axis explicitly.

Examples:
- `cz r` = cylinder parallel to `z`
- `c/x ...` = cylinder parallel to `x`
- `c/y ...` = cylinder parallel to `y`

Do not infer "parallel pipes" from spacing alone. Check the cylinder axis type first.

### Reflective Boundaries
Call out reflective boundaries explicitly. In MCNP, starred surfaces such as `*17 px ...` are reflective. State whether:
- all outer planes are reflective
- only some are reflective
- the model is a repeated lattice cell or a finite bounded problem

### Water / Outside Region
For moderator or void cells, rewrite them as boolean subtraction:

```text
inside box
minus pipe 1 outer region
minus pipe 2 outer region
minus any excluded voids
```

This is almost always clearer than reading the raw cell card directly.

## Style Rules
- Prefer short sections and compact tables.
- Use ASCII when it clarifies centers, axes, offsets, or nesting.
- Use line references whenever making a concrete claim about a card.
- Avoid over-explaining basic MCNP syntax once the sign rule is established.
- Do not present an undifferentiated dump of all cards unless the user explicitly asks for the raw deck.
- If the deck appears mislabeled, say so directly and explain why using the surface types.

## Fast Verification Template
When the user wants the shortest useful explanation, compress the answer to:

1. one-paragraph model summary
2. surface legend
3. one ASCII plane view
4. cell recipe cheat sheet
5. invariants checklist

Use this compact pattern:

```text
Surfaces:
z-pipe: 11 -> 2 -> 1
x-pipe: 14 -> 12 -> 13
box: x in [...], y in [...], z in [...], reflective

Cells:
5 = z gas
4 = z fuel
1 = z wall
7 = x gas
6 = x fuel
8 = x wall
3 = water inside box, outside both pipes
```

## If Asked To Compare To OpenMC
After the MCNP explanation is stable:
- identify the surface families that need OpenMC equivalents
- identify the boundary conditions
- identify material parity requirements
- distinguish exact deck parity from workbook-aligned simplifications

Do not jump into code until the geometry interpretation is clear.
