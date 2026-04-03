# OpenMC Model Interface Refactor Plan

## Goal

Introduce a formal OpenMC model interface for `models/<name>/openmc/model.py` without changing model behavior or numerical results.

The refactor should:

- standardize the callable surface for every OpenMC model
- move OpenMC model implementations to explicit classes
- keep the current template layer in `models/<name>/__init__.py`
- preserve current physics, geometry, settings, and plotting behavior
- verify each model migration before proceeding to the next model

## Proposed Interface

Each `models/<name>/openmc/model.py` should export a single concrete class that inherits from `OMCModel`.

Required methods:

- `create_materials(params)`
- `build_model(params)`
- `create_settings(params, dims)`

Required for current repo behavior:

- `create_plots(dims, materials)`

Notes:

- `params` remains the fully derived parameter dictionary produced by the `Template` in `models/<name>/__init__.py`.
- `build_model(params)` continues to return `(materials, geometry, dims)` to minimize churn.
- `dims` is retained for now even though the name is imperfect.
- This is an interface refactor, not a physics or reporting refactor.

## Current State

Today the repo uses two separate contracts:

- `models/<name>/__init__.py` exports `Template`, a `ProblemTemplate` subclass used by the runner for schema/defaults/derived params.
- `models/<name>/openmc/model.py` is imported as a raw module and the solver calls module-level functions:
  - `build_model(...)`
  - `create_settings(...)`
  - `create_plots(...)`

This works, but the OpenMC side is only duck-typed and not explicitly enforced.

## Target State

The runner remains unchanged at the template layer.

The OpenMC solver should load an `OMCModel` instance rather than a raw module object. Each OpenMC model file should contain a single explicit class, for example:

- `CylinderArray`
- `CentrifugeUnitCell`
- `PipeCrossModel`
- `PipeUnitCell`

The loader should discover and instantiate the concrete `OMCModel` subclass from `openmc/model.py`.

## Non-Goals

- changing parameter schemas
- renaming or restructuring `dims`
- changing solver math or source placement behavior
- changing validation plot content
- changing certification baselines during the migration
- introducing shared dataclasses or rigid typed return objects

## Migration Strategy

This refactor should not convert every model first and validate at the end.

Instead, the migration should proceed one model at a time:

1. migrate one OpenMC model to `OMCModel`
2. run its model tests
3. rerun the relevant certification/parity basis for that model
4. confirm the new results are nearly identical to the pre-refactor OpenMC basis
5. only then proceed to the next model

The first model-specific gate is `cylinder-array`, using the current `CB-16` blending-system basis as the acceptance reference.

For this plan, "holds" means:

- no intended change in physics or derived geometry behavior
- no structural change in the generated study outputs beyond the class-based interface migration
- OpenMC numerical results remain nearly identical to the original pre-refactor OpenMC results for the selected basis run

Any material numerical deviation should stop the sequence until understood.

## Refactor Steps

### Step 1. Define the Base Interface

Add a base ABC in `critbuddy/solvers/openmc/`, named `OMCModel`, with the required method surface:

- `create_materials(params)`
- `build_model(params)`
- `create_settings(params, dims)`
- `create_plots(dims, materials)`

This step is interface-only. No existing models or solver code should change behavior yet.

Acceptance criteria:

- `OMCModel` exists in a stable import location under `critbuddy/solvers/openmc/`
- the ABC documents the required methods and their intended semantics
- no solver behavior changes are introduced in this step
- existing tests unrelated to the new interface continue to pass

### Step 2. Add an OpenMC Model Loader

Add a dedicated loader that imports `models/<name>/openmc/model.py`, finds the concrete `OMCModel` subclass, instantiates it, and returns the instance.

During migration, the loader may temporarily support a compatibility fallback for legacy module-level-function models, but that fallback is transitional and should be removed at the end.

Acceptance criteria:

- a new loader exists for OpenMC model instances
- the loader returns a concrete `OMCModel`
- the loader errors clearly when no concrete model class is found
- the loader errors clearly when multiple candidate model classes are found
- unit tests cover the discovery behavior

### Step 3. Switch the Solver to the New Loader

Update `critbuddy/solvers/openmc/solver.py` to use the OpenMC model loader and call instance methods on the returned `OMCModel`.

No geometry, settings, plotting, or output behavior should change in this step.

Acceptance criteria:

- the OpenMC solver no longer relies on raw module-level duck typing
- the solver uses:
  - `model.build_model(...)`
  - `model.create_settings(...)`
  - `model.create_plots(...)`
- the existing integration tests for current OpenMC models still pass
- run-local outputs remain structurally unchanged

### Step 4. Migrate One Reference Model First

Migrate `models/cylinder-array/openmc/model.py` to a class-based implementation:

- add `class CylinderArray(OMCModel)`
- move the current OpenMC functions into methods
- preserve logic exactly

This model should be the reference pattern for the remaining conversions.

Acceptance criteria:

- `CylinderArray` inherits from `OMCModel`
- the implementation preserves the same build/settings/plot behavior
- `tests/integration/models/test_cylinder_array.py` passes
- any relevant validation outputs remain unchanged in structure
- the current `CB-16` blending-system basis is rerun against the migrated `cylinder-array` model
- the migrated `cylinder-array` OpenMC results are nearly identical to the original pre-refactor OpenMC basis for `CB-16`
- no other OpenMC model is migrated until the `CB-16` gate passes

### Step 5. Migrate `centrifuge-unit-cell`

Convert `models/centrifuge-unit-cell/openmc/model.py` to an explicit `OMCModel` subclass.

Keep the migration mechanical: move functions into methods without changing model behavior.

Acceptance criteria:

- `CentrifugeUnitCell` inherits from `OMCModel`
- the relevant centrifuge model tests pass
- the relevant centrifuge certification/parity basis is rerun
- the migrated OpenMC results are nearly identical to the original pre-refactor OpenMC basis
- `pipe-cross-model` and `pipe-unit-cell` are not migrated until this gate passes

### Step 6. Migrate `pipe-cross-model`

Convert `models/pipe-cross-model/openmc/model.py` to an explicit `OMCModel` subclass.

Acceptance criteria:

- `PipeCrossModel` inherits from `OMCModel`
- the relevant pipe-cross model tests pass
- the relevant pipe-cross certification/parity basis is rerun
- the migrated OpenMC results are nearly identical to the original pre-refactor OpenMC basis
- `pipe-unit-cell` is not migrated until this gate passes

### Step 7. Migrate `pipe-unit-cell`

Convert `models/pipe-unit-cell/openmc/model.py` to an explicit `OMCModel` subclass.

Acceptance criteria:

- `PipeUnitCell` inherits from `OMCModel`
- the relevant pipe-unit-cell model tests pass
- the relevant pipe-unit-cell certification/parity basis is rerun
- the migrated OpenMC results are nearly identical to the original pre-refactor OpenMC basis

### Step 8. Remove the Compatibility Fallback

Once all maintained OpenMC models are class-based, remove any temporary legacy fallback from the OpenMC model loader.

At that point, the class-based interface becomes the only supported interface.

Acceptance criteria:

- the loader requires a concrete `OMCModel` subclass
- legacy raw-module OpenMC models are no longer supported
- failure messages are clear when the contract is violated
- tests cover the strict loader behavior

### Step 9. Final Regression Confirmation

After all per-model migration gates have passed, do a final review of the migrated certification/parity outputs to confirm the interface refactor did not introduce unresolved drift anywhere in the maintained OpenMC model set.

This is a final confirmation step, not the first time results are being checked.

Acceptance criteria:

- each migrated model has already passed its model-specific parity gate
- certification artifacts are updated only where the rerun basis has been reviewed and accepted
- any numerical deltas are investigated before treating the refactor as complete
- the refactor is not considered done until parity is re-established across the maintained migrated models

## Implementation Rules

- Do not change model physics during the interface migration.
- Do not mix cleanup refactors with the interface refactor.
- Keep method bodies mechanically close to the current module functions.
- Favor one model migration at a time over a big-bang conversion.
- Do not start the next model migration until the current model's certification/parity gate passes.
- If needed, land the solver/loader changes before all model migrations are complete, but keep the compatibility fallback explicitly temporary.

## Definition of Done

The refactor is complete when all of the following are true:

- every maintained OpenMC model inherits from `OMCModel`
- the OpenMC solver runs against `OMCModel` instances, not raw modules
- the compatibility fallback has been removed
- model integration tests pass
- each migrated model has passed its own certification/parity gate before the next model began
- certification/parity reruns confirm no unintended behavior change
