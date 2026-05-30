# M1693 Paper-Route Controller-Family Full Rollout Execution

- status: completed
- result class: `controller_family_full_rollout_execution_pass`
- artifact: `runs/m1693_controller_family_full_rollout_execution/summary.json`
- parent design: `docs/m1692-paper-route-controller-family-full-rollout-execution-design.md`
- executable workload: `runs/m1690_controller_family_executable_workload_materialization_preflight/executable_workload_matrix.csv`

## Summary

M1693 executed the full public controller-family rollout over the materialized
M1690 workload.

This milestone ran public evaluation only. It did not train, replay, run PPO,
promote, use private holdout, change actor inputs, tune a profile, or claim
controller-family ranking, paper-level evidence, or level3 self-identification.

## Execution Result

- episode count: `864`
- target episode count: `864`
- profile count: `12`
- spec count: `72`
- failure count: `0`
- selected metrics finite: `true`
- guardrail violation count: `0`
- environment rollout started: `true`
- training started / replay started / PPO used: `false` / `false` / `false`
- private holdout used / promoted / actor input contract changed: `false` / `false` / `false`

Required artifacts were written:

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

## Aggregate Shape

- profile aggregate rows: `12`
- spec aggregate rows: `72`
- stratum aggregate rows: `5`
- comparison aggregate rows: `11`
- failure rows: `0`

The `failure_rows.csv` artifact exists with a stable header even though no cell
failed.

## Diagnostic Profile Snapshot

The following values are raw public-rollout diagnostics and must not be treated
as a controller-family ranking until M1694 audits the task quality and comparison
semantics.

| profile | success_rate | collision_rate | clearance_margin_mean |
| --- | ---: | ---: | ---: |
| L0_current_masked | 0.0278 | 0.1389 | 8.0118 |
| L1_one_step | 0.0139 | 0.1806 | 8.8889 |
| L2_window_13 | 0.0000 | 0.0139 | 11.2508 |
| L2_window_13_current_tiled | 0.0000 | 0.0000 | 12.8483 |
| L2_window_25 | 0.0000 | 0.0000 | 11.8848 |
| L2_window_25_current_tiled | 0.0000 | 0.0000 | 12.4119 |
| L2_window_50 | 0.0000 | 0.0000 | 12.2862 |
| L2_window_50_current_tiled | 0.0000 | 0.0000 | 11.5513 |
| L2_window_100 | 0.0000 | 0.0278 | 11.1310 |
| L2_window_100_current_tiled | 0.0000 | 0.0000 | 11.5585 |
| L3_online_gru | 0.1667 | 0.0972 | 7.4968 |
| L3_reset_control_corrected | 0.2361 | 0.0694 | 7.6256 |

## Supported Claims

- The materialized 72-spec x 12-profile public rollout is executable
  end-to-end.
- The M1693 runner is resumable and writes the required episode, aggregate,
  failure, summary, and run-state artifacts.
- The execution preserved the no-training, no-replay, no-PPO, no-promotion,
  no-private-holdout, and no-actor-input-change guardrails.

## Unsupported Claims

- controller-family ranking
- recurrent advantage
- finite-window history necessity
- paper-level evidence
- private-holdout evidence
- level3 anticipatory self-identification

## Decision

M1693 passes as public full-rollout execution. Route to M1694 result audit before
interpreting the profile, spec, stratum, or comparison aggregates.
