# M1692 Paper-Route Controller-Family Full Rollout Execution Design

- status: completed
- decision: `full_rollout_execution_design_admit_resumable_implementation`
- parent audit: `docs/m1691-paper-route-controller-family-executable-workload-materialization-result-audit.md`
- executable specs: `runs/m1690_controller_family_executable_workload_materialization_preflight/executable_task_specs.json`
- executable workload: `runs/m1690_controller_family_executable_workload_materialization_preflight/executable_workload_matrix.csv`

## Summary

M1692 designs the first full public measured rollout execution after executable
workload materialization passed audit.

This milestone is design-only. It does not run environment rollout, train,
replay, run PPO, use private holdout, promote, change actor inputs, or claim
controller-family ranking, paper-level evidence, or level3 self-identification.

## Execution Target

M1693 may execute the public workload:

```text
task specs: 72
controller profiles: 12
workload cells: 864
source artifacts:
  runs/m1690_controller_family_executable_workload_materialization_preflight/executable_task_specs.json
  runs/m1690_controller_family_executable_workload_materialization_preflight/executable_workload_matrix.csv
profile artifacts:
  runs/m1674_controller_family_one_seed_public_pilot/configs/*_seed167400.json
  runs/m1674_controller_family_one_seed_public_pilot/profile_runs/*/seed_167400/checkpoint.pt
```

The rollout remains public evaluation-only evidence. It is not a promotion gate
and not a private holdout.

## Runner Requirements

The M1693 runner must:

```text
load executable_task_specs.json;
load executable_workload_matrix.csv;
load the M1674 profile config/checkpoint for each workload row;
construct env config from the executable spec;
override only history_length to match the profile config;
preserve P0/no-wheel/no-oracle actor contract;
wrap the env with the profile mask/reset behavior;
verify env observation dim equals checkpoint model obs_dim;
run exactly one deterministic episode per workload_id;
write episode_rows incrementally;
write failure_rows for exceptions instead of silently dropping rows;
write summary and aggregates only after execution completes or stops;
```

It must not:

```text
train;
run replay;
run PPO;
promote;
use private holdout;
change actor inputs;
use profile-specific tuning;
drop failed cells silently;
claim controller-family ranking.
```

## Resumability

The runner must be resumable.

Required behavior:

- `episode_rows.csv` is append-only by `workload_id`.
- If `--resume` is used, existing completed `workload_id`s are skipped.
- `failure_rows.csv` records `workload_id`, profile, spec, error type, and
  message.
- `run_state.json` records started/completed/failed counts and latest timestamp.
- Re-running the same command must not duplicate rows.

This prevents losing evidence or needing a full rerun if one profile/spec cell
fails.

## Required Artifacts

M1693 should write:

```text
runs/m1693_controller_family_full_rollout_execution/summary.json
runs/m1693_controller_family_full_rollout_execution/episode_rows.csv
runs/m1693_controller_family_full_rollout_execution/profile_aggregate.csv
runs/m1693_controller_family_full_rollout_execution/spec_aggregate.csv
runs/m1693_controller_family_full_rollout_execution/stratum_aggregate.csv
runs/m1693_controller_family_full_rollout_execution/comparison_aggregate.csv
runs/m1693_controller_family_full_rollout_execution/failure_rows.csv
runs/m1693_controller_family_full_rollout_execution/run_state.json
```

## Metrics

Episode rows must include at least:

```text
workload_id
task_source_id
profile_name
task_family
source_edge
window_tag
strata
success
collision
min_clearance_margin
return
steps
action_rate_mean
high_sideslip_fraction
termination flags
guardrail flags
```

Aggregate metrics:

```text
success_rate
collision_rate
clearance_margin_mean
clearance_margin_p10
return_mean
steps_mean
control_smoothness
spin_or_unstable_rate
failure_rate
```

Comparison aggregates must include:

```text
L2 normal minus matched L2 current-tiled
L3 online minus L3 reset-control
L3 online minus best L2 normal
L1 one-step versus history-capable profiles
T4 versus T5 strata
explicit-window subset versus all_72_specs
mapping-window-unspecified diagnostic stratum
```

Comparison aggregates are diagnostic only until M1694 audits them.

## Success Criteria

M1693 execution passes as public rollout plumbing if:

```text
episode_count == 864
profile_count == 12
spec_count == 72
failure_count == 0
all selected metrics are finite
guardrail_violation_count == 0
training_started == false
replay_started == false
ppo_used == false
private_holdout_used == false
promoted == false
actor_input_contract_changed == false
controller_family_ranking_claim_made == false
level3_self_id_claim_made == false
```

If any cell fails, M1693 should write complete failure artifacts and route to an
audit/repair milestone instead of rerunning with changed scope.

## Runtime Budget

M1686 routed 48 episodes quickly. M1693 is 18x larger. Use CPU by default and
single-process deterministic execution first; parallelization can be added
later only if the single-process runner is correct and resumable.

Expected budget:

```text
CPU device
OMP_NUM_THREADS=1
MKL_NUM_THREADS=1
single process
864 episodes
```

If runtime is unexpectedly high, stop after writing partial artifacts and route
to performance/resume audit. Do not reduce the workload silently.

## Next Step

Admit M1693 resumable full rollout execution implementation. M1693 may run the
public 864-cell environment rollout under the above guardrails, but it still
must not interpret results as ranking evidence until M1694 audit.
