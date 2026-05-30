# M1792 Executable V2 Reset-Feasibility Adapter Implementation

- status: completed
- decision: `executable_v2_reset_adapter_implementation_pass_route_to_execution_design`
- module: `src/autodrift/executable_v2_reset_feasibility_preflight.py`
- test: `tests/test_executable_v2_reset_feasibility_preflight.py`
- full 312-row reset preflight: not run
- rollout/training/replay/PPO: false

## Summary

M1792 implements a reset-only adapter for M1790 executable v2 panel specs. The
adapter reads `executable_v2_panel_specs.json`, iterates
`executable_v2_panel_specs`, uses each spec's `env_config`, and writes reset
diagnostic rows while preserving v2 metadata.

The implementation intentionally does not run the real 312-row reset preflight.
Focused tests use a monkeypatched environment and verify the adapter contract.

Implemented outputs:

```text
summary.json
reset_stress_rows.csv
sampling_failure_rows.csv
label_distribution_by_surface.csv
label_distribution_by_profile.csv
label_distribution_by_hidden_bucket.csv
```

Preserved row fields include:

```text
v2_panel_spec_id
source_v1_bounded_panel_spec_id
v2_role_surface_id
profile_name
v2_task_label
hidden_dynamics_bucket
road_boundary_bucket
obstacle_timing_bucket
obstacle_lateral_bucket
v2_primary_metric
v2_admissibility_gate
reset_ready_spec
diagnostic_only_no_ranking_claim
v2_ranking_admissible_by_default
```

## Verification

Focused test:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m pytest tests/test_executable_v2_reset_feasibility_preflight.py -q
```

Result:

```text
2 passed in 0.93s
```

The tests verify:

- successful reset-only adapter output over a small v2 spec payload;
- preservation of v2 identifiers and role metadata;
- no label leakage or ranking admission;
- sampling failure preservation with `v2_panel_spec_id` and error text;
- no policy action, rollout, training, replay, PPO, promotion, ranking, or
  paper-level claim.

## Guardrails

- full 312-row reset preflight run: `false`
- environment rollout started: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Claim Boundary

Supported:

- executable v2 reset-feasibility adapter exists;
- focused tests pass;
- adapter preserves v2 metadata and failure rows.

Unsupported:

- full 312-row reset feasibility result;
- measured execution;
- controller-family ranking;
- profile promotion;
- private-holdout evidence;
- paper-level benchmark evidence;
- level3 self-identification.

## Decision

Route to M1793 executable v2 reset-feasibility execution design. M1793 should
fix the exact command, input artifact, output directory, target counts, and
guardrails before the real 312-row reset preflight is run.
