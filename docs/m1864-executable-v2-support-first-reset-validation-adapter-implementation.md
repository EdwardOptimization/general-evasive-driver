# M1864 Executable V2 Support-First Reset Validation Adapter Implementation

- status: completed
- decision: `support_first_reset_validation_adapter_implementation_pass_route_to_execution_design`
- branch: `paper_route_executable_v2_support_first_reset_validation`
- parent design: `docs/m1863-executable-v2-support-first-reset-validation-design.md`
- source module: `src/autodrift/executable_v2_support_first_reset_validation_adapter.py`
- focused tests: `tests/test_executable_v2_support_first_reset_validation_adapter.py`
- project artifact conversion run: `false`
- environment reset run: `false`
- rollout/training/replay/PPO: `false`

## Purpose

M1863 blocked direct reset validation over the M1861 support-first
materialized specs because the rows did not yet contain the standard
`executable_v2_panel_specs` reset payload fields. M1864 implements the
no-reset adapter that performs that schema conversion in code, with synthetic
focused tests only.

This milestone does not run the adapter over the project M1861 artifacts. It
only verifies that the adapter can produce the intended payload shape and that
the guardrails remain explicit.

## Implemented Adapter

The new adapter reads a support-first materialized JSON payload containing:

```text
executable_v2_panel_specs
```

and can write the following no-reset artifacts:

```text
summary.json
support_first_reset_executable_v2_panel_specs.json
support_first_reset_executable_v2_panel_specs.csv
support_first_reset_validation_matrix.csv
support_first_reset_missing_field_rows.csv
support_first_reset_duplicate_key_rows.csv
support_first_reset_validation_claim_boundary.csv
```

Each converted row now includes the reset-preflight fields required by the
M1863 contract, including:

```text
v2_panel_spec_id
profile_config_path
v2_role_surface_id
role_panel_id
v2_primary_metric
v2_admissibility_gate
reset_ready_spec
diagnostic_only_no_ranking_claim
measured_execution_admissible
controller_family_ranking_admissible
environment_reset_scheduled
environment_rollout_scheduled
training_scheduled
```

The deterministic mappings follow M1863:

```text
v2_panel_spec_id = materialized_v2_panel_spec_id
v2_role_surface_id = source_role_semantics + "::" + surface_variant
role_panel_id = source_role_semantics
hidden_dynamics_bucket = "mu_" + mu + "::" + surface_variant
road_boundary_bucket = "circle_r18"
obstacle_timing_bucket = surface_variant
obstacle_lateral_bucket = "support_first_width_" + obstacle_half_width
```

The adapter preserves each row's inline `env_config` and only adds reset
preflight plumbing defaults when missing, such as `history_length=1`,
`include_privileged_params=false`, `obstacle_relative_velocity_mode=zero`, and
`wheel_observation_mode=none`.

## Focused Validation

Command run:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m pytest tests/test_executable_v2_support_first_reset_validation_adapter.py -q
```

Result:

```text
3 passed in 0.12s
```

The focused tests cover:

- executable-v2 reset payload shape;
- env-config preservation plus reset-preflight plumbing defaults;
- no label leakage into actor input;
- reset-ready and reset-validation flags;
- ranking and measured-execution blocks;
- duplicate key detection;
- missing required field detection;
- claim boundary rows blocking reset, measured execution, ranking, and level3
  self-ID claims.

## Claim Boundary

Supported by M1864:

```text
support-first reset-validation adapter implementation
focused synthetic conversion tests
no-reset payload schema checks
```

Not supported by M1864:

```text
project artifact conversion result
reset feasibility
measured execution
controller-family ranking
paper-level evidence
level3 self-identification evidence
```

## Route Decision

Route to:

```text
m1865-executable-v2-support-first-reset-validation-adapter-execution-design
```

M1865 should pre-register the exact no-reset command that runs this adapter
over the M1861 project artifacts with fixed target counts. It must still not
run environment reset, rollout, measured execution, training, replay, PPO,
ranking, or paper-level claims.

## Guardrails

- project artifact conversion run: `false`
- environment reset started: `false`
- environment rollout started: `false`
- policy action executed: `false`
- measured rollout started: `false`
- training/replay/PPO: `false`
- actor input contract changed: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`
