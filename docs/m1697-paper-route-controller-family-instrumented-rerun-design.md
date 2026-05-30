# M1697 Paper-Route Controller-Family Instrumented Rerun Design

- status: completed
- decision: `instrumented_rerun_design_admit_public_execution`
- parent implementation: `docs/m1696-paper-route-controller-family-outcome-semantics-instrumentation-implementation.md`

## Summary

M1697 designs the instrumented rerun needed after M1696 added logging-only
outcome semantics.

This milestone is design-only. It does not execute the full rerun, train,
replay, run PPO, promote, use private holdout, tune profiles, change actor
inputs, or claim controller-family ranking, paper-level evidence, or level3
self-identification.

## Execution Target

M1698 may rerun the exact public M1693 workload with instrumentation enabled:

```text
task specs: 72
controller profiles: 12
workload cells: 864
workload: runs/m1690_controller_family_executable_workload_materialization_preflight/executable_workload_matrix.csv
specs: runs/m1690_controller_family_executable_workload_materialization_preflight/executable_task_specs.json
profile checkpoints: runs/m1674_controller_family_one_seed_public_pilot/profile_runs/*/seed_167400/checkpoint.pt
eval_seed_base: 169300
device: cpu
threads: OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
```

The rerun must preserve the M1693 workload, profile checkpoints, deterministic
seed assignment, and actor input contract. It may differ only by logging the
M1696 outcome-semantics fields.

## Command

Recommended M1698 command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.controller_family_full_rollout_execution \
  --output-dir runs/m1698_controller_family_instrumented_full_rollout \
  --device cpu \
  --no-resume
```

## Required Artifacts

M1698 should write:

```text
runs/m1698_controller_family_instrumented_full_rollout/summary.json
runs/m1698_controller_family_instrumented_full_rollout/episode_rows.csv
runs/m1698_controller_family_instrumented_full_rollout/profile_aggregate.csv
runs/m1698_controller_family_instrumented_full_rollout/spec_aggregate.csv
runs/m1698_controller_family_instrumented_full_rollout/stratum_aggregate.csv
runs/m1698_controller_family_instrumented_full_rollout/comparison_aggregate.csv
runs/m1698_controller_family_instrumented_full_rollout/outcome_aggregate.csv
runs/m1698_controller_family_instrumented_full_rollout/termination_reason_aggregate.csv
runs/m1698_controller_family_instrumented_full_rollout/profile_outcome_aggregate.csv
runs/m1698_controller_family_instrumented_full_rollout/failure_rows.csv
runs/m1698_controller_family_instrumented_full_rollout/run_state.json
```

## Pass Checks

M1698 execution passes as an instrumented public rollout if:

```text
episode_count == 864
profile_count == 12
spec_count == 72
failure_count == 0
selected metrics are finite
guardrail_violation_count == 0
outcome_aggregate_rows > 0
termination_reason_aggregate_rows > 0
profile_outcome_aggregate_rows > 0
episode rows contain termination_reason
episode rows contain obstacle_passed_raw
episode rows contain completion_reason
episode rows contain outcome_bucket
```

## Claim Boundary

M1698 may claim only:

```text
instrumented public rerun execution status
artifact completeness
outcome-semantics availability for later audit
```

M1698 must not claim:

```text
controller-family ranking
finite-window history necessity
recurrent advantage
private-holdout generalization
paper-level evidence
level3 anticipatory self-identification
```

## Decision

Admit M1698 instrumented public rerun execution. Interpret the new outcome
aggregates only in a later audit milestone.
