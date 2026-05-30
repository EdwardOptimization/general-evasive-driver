# M1809 Executable V2 Stable Source Materialization Implementation

- status: completed
- decision: `stable_source_materialization_implementation_pass_route_to_execution_design`
- module: `src/autodrift/executable_v2_stable_source_materialization.py`
- test: `tests/test_executable_v2_stable_source_materialization.py`
- focused test command: `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest tests/test_executable_v2_stable_source_materialization.py -q`
- focused test result: `2 passed in 0.12s`
- full test command: `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q`
- full test result: `1734 passed, 4 warnings in 10.13s`
- project artifact execution: `false`
- reset run: `false`
- rollout started: `false`
- measured rollout started: `false`
- training/replay/PPO: `false`

## Summary

M1809 implements the no-reset stable source materializer designed in M1808. The
helper reads stable new-materialization needs, top-up candidate rows, bounded
panel specs, and the bounded panel matrix profile controls, then writes
materialization planning artifacts without running reset, rollout, measured
execution, or project artifact execution.

The implementation creates new materialized source ids instead of mutating
unsupported M1771 sources in place. It clones the target env config as source
basis, applies a label-specific stable sampler repair, records provenance, and
marks every materialized source as requiring reset validation.

## Implemented Artifacts

The helper writes:

```text
summary.json
stable_source_materialization_targets.csv
stable_source_materialization_specs.csv
stable_source_materialization_specs.json
stable_source_materialization_matrix.csv
stable_source_materialization_duplicate_keys.csv
stable_source_materialization_claim_boundary.csv
```

The claim boundary keeps repaired reset feasibility, measured execution, and
controller-family ranking blocked.

## Implemented Behavior

Materialized source specs include:

```text
stable_materialization_key
materialized_source_scenario_spec_id
materialized_bounded_panel_spec_id
source_basis_bounded_panel_spec_id
source_basis_support_status
near_candidate_ids
materialization_strategy
sampler_repair_variant_id
env_config_delta_json
profile_control_count
profile_controls_preserved
labels_enter_actor_input
reset_validation_required
measured_execution_admissible
controller_family_ranking_admissible
duplicate_key_detected
```

The label-specific env-config patch sets:

```text
obstacle.allowed_labels = [target_label]
obstacle.max_sample_attempts >= 1000
obstacle.require_aeb_infeasible = true  for aes_feasible
obstacle.require_aeb_infeasible = false for aeb_feasible
```

This is source materialization support logic, not actor input logic.

## Focused Test Coverage

Focused tests cover:

- three target materialization specs;
- materialized source and bounded-panel id generation;
- profile-control matrix expansion;
- `aes_feasible` and `aeb_feasible` env-config label-specific patches;
- provenance from metadata-only unsupported and near-candidate rows;
- no-label-leakage and reset-validation-required flags;
- duplicate-key rejection and duplicate artifact output;
- claim-boundary outputs.

No project artifact materialization occurred.

## Route Decision

Route to:

```text
m1810-executable-v2-stable-source-materialization-execution-design
```

M1810 should fix the exact command and expected counts for running this helper
on M1805/M1771 artifacts. Execution must remain a separate milestone.

## Guardrails

- environment reset started: `false`
- environment rollout started: `false`
- policy action executed: `false`
- measured rollout started: `false`
- project artifact execution: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- reward changed: `false`
- dynamics changed: `false`
- termination behavior changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Claim Boundary

Supported:

- no-reset stable source materializer implementation;
- focused tests for materialization targets, duplicate detection, provenance,
  profile controls, env-config patching, and claim boundaries.

Unsupported:

- project-artifact source materialization result;
- repaired reset feasibility pass;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
