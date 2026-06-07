# M3014 Engineering Controller Route A Post-Residual-Stop New Source Bounded Execution Admission Design

## Metadata

- status: completed
- decision: `admit_m3015_bounded_execution_preflight`
- manifest: `experiments/manifests/m3014-engineering-controller-route-a-post-residual-stop-new-source-bounded-execution-admission-design.json`
- design artifact: `docs/m3014-engineering-controller-route-a-post-residual-stop-new-source-bounded-execution-admission-design.md`
- parent synthesis: `docs/m3013-engineering-controller-route-a-post-residual-stop-new-source-executable-env-materialization-result-audit.md`
- parent materialization summary: `runs/m3012_engineering_controller_route_a_post_residual_stop_new_source_executable_env_materialization_preflight/summary.json`
- follow-up manifest: `experiments/manifests/m3015-engineering-controller-route-a-post-residual-stop-new-source-bounded-execution-preflight.json`
- next: `m3015-engineering-controller-route-a-post-residual-stop-new-source-bounded-execution-preflight`

M3014 is design-only. It does not reset, step, rollout, replay, validate,
train, rank, promote, mutate checkpoints, or compute a performance verdict.

## Design Decision

M3014 admits M3015 as a bounded no-training no-ranking execution preflight over
the complete M3012 denominator:

```text
source specs: 16 M3012 executable source specs
profile bindings: 2 read-only profile bindings
workload rows: 32 M3012 executable workload rows
episodes per workload row: 1
total scheduled episodes: 32
checkpoint mutation: false
profile-specific tuning: false
ranking or winner selection: false
```

M3015 may execute current-sim rollouts only to collect diagnostic closed-loop
rows. It must not convert those rows into repair-success, validation,
performance, paper, high-fidelity, finite-window-vs-GRU, full-driver, or
self-identification claims.

## Adapter Contract

M3015 must adapt the M3012 artifacts before execution:

```text
read executable_source_specs.json as env-config authority
read executable_workload_rows.csv as workload denominator authority
normalize executable_workload_id to workload_id for runtime compatibility
normalize profile_binding_name to profile_name for runtime compatibility
join by task_source_id and executable_source_spec_id
load checkpoints and configs read-only
preserve actor observation 72 and action 3
assert the human-view env contract before every episode
write failures instead of dropping rows
```

The current `controller_family_full_rollout_execution.py` helper is useful for
runtime primitives, but M3015 needs a dedicated adapter because M3012 workload
rows are candidate/parent Route A bindings rather than the old M1690
controller-family profile matrix.

## Required M3015 Artifacts

M3015 must write:

```text
runs/m3015_engineering_controller_route_a_post_residual_stop_new_source_bounded_execution_preflight/summary.json
runs/m3015_engineering_controller_route_a_post_residual_stop_new_source_bounded_execution_preflight/execution_workload_rows.csv
runs/m3015_engineering_controller_route_a_post_residual_stop_new_source_bounded_execution_preflight/episode_rows.csv
runs/m3015_engineering_controller_route_a_post_residual_stop_new_source_bounded_execution_preflight/failure_rows.csv
runs/m3015_engineering_controller_route_a_post_residual_stop_new_source_bounded_execution_preflight/profile_aggregate_rows.csv
runs/m3015_engineering_controller_route_a_post_residual_stop_new_source_bounded_execution_preflight/source_aggregate_rows.csv
runs/m3015_engineering_controller_route_a_post_residual_stop_new_source_bounded_execution_preflight/claim_boundary_rows.csv
runs/m3015_engineering_controller_route_a_post_residual_stop_new_source_bounded_execution_preflight/execution_guard_rows.csv
runs/m3015_engineering_controller_route_a_post_residual_stop_new_source_bounded_execution_preflight/gate_matrix.csv
runs/m3015_engineering_controller_route_a_post_residual_stop_new_source_bounded_execution_preflight/run_state.json
docs/m3015-engineering-controller-route-a-post-residual-stop-new-source-bounded-execution-preflight.md
experiments/manifests/m3016-engineering-controller-route-a-post-residual-stop-new-source-bounded-execution-result-audit.json
```

## Gate Contract

M3015 must pass only if:

```text
M3013 synthesis doc exists
M3012 summary status_pass true
M3012 gate_matrix_pass true
16 executable source specs are present
32 executable workload rows are present
32 workload rows are scheduled exactly once
all failures are recorded, not dropped
actor observation 72 and action 3 remain unchanged
no hidden/oracle/future-target/source/route/outcome/progress/verdict/TTC actor input
no training, replay training, PPO, ranking, winner selection, checkpoint mutation, or promotion
M3016 result-audit manifest is written before interpretation
```

M3015 may fail as an execution preflight if some rows cannot load or run. Such
failures must be recorded in `failure_rows.csv` and audited by M3016; they must
not be repaired by dropping rows.

## Supported And Unsupported Claims

Supported M3014 claim:

```text
M3015 bounded diagnostic execution preflight is precisely scoped.
```

Unsupported claims:

```text
execution result exists
validation result exists
repair succeeded
driver performance improved
paper evidence exists
current-sim verdict changed
high-fidelity validation is ready
finite-window-vs-GRU result exists
full ideal driver gate passed
level3 self-identification evidence exists
ranking or promotion is justified
```

## Next

M3015 should implement the bounded execution preflight and register M3016
result audit. M3015 must keep the 32-row denominator intact and report all
rows, successful or failed, before any interpretation.
