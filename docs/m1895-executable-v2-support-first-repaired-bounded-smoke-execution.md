# M1895 Executable V2 Support-First Repaired Bounded-Smoke Execution

- status: completed
- decision: `support_first_repaired_bounded_smoke_execution_pass_route_to_result_audit`
- branch: `paper_route_executable_v2_support_first_measured_execution`
- command design: `docs/m1894-executable-v2-support-first-repaired-bounded-smoke-execution-command-design.md`
- summary: `runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/summary.json`
- training/replay/PPO: false
- controller-family ranking claim made: false
- paper-level claim made: false
- level3 self-ID claim made: false

## Command

Executed the exact M1894 command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.executable_v2_support_first_repaired_bounded_smoke_execution \
  --support-first-repaired-measured-specs \
  runs/m1889_executable_v2_support_first_repaired_runner_adapter_preflight/repaired_measured_executable_specs.json \
  --support-first-repaired-workload \
  runs/m1889_executable_v2_support_first_repaired_runner_adapter_preflight/repaired_measured_workload_matrix.csv \
  --support-first-repaired-import-rows \
  runs/m1889_executable_v2_support_first_repaired_runner_adapter_preflight/repaired_measured_import_rows.csv \
  --source-episode-rows \
  runs/m1880_executable_v2_support_first_measured_runner_execution/episode_rows.csv \
  --m1674-run-dir runs/m1674_controller_family_one_seed_public_pilot \
  --eval-seed-base 189500 \
  --device cpu \
  --output-dir runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution \
  --no-resume \
  --next-blocker m1896-executable-v2-support-first-repaired-bounded-smoke-execution-result-audit
```

The command completed with return code `0`.

## Summary

`summary.json` reports:

```text
result_class: executable_v2_support_first_repaired_bounded_smoke_execution_pass
rollout_episode_count: 576 / 576
import_episode_count: 384 / 384
total_panel_row_count: 960 / 960
failure_count: 0
import_failure_count: 0
source_episode_join_missing_count: 0
controller_profile_count: 12 / 12
selected_source_spec_count: 16 / 16
repaired_executable_spec_count: 48 / 48
role_panel_count: 4 / 4
role_surface_count: 8 / 8
repair_variant_count: 5 / 5
rollout_variant_count: 3 / 3
import_variant_count: 2 / 2
profile_alias_mismatch_count: 0
duplicate_panel_row_count: 0
all_selected_metrics_finite: true
metric_completeness_passed: true
metric_completeness_failure_count: 0
guardrail_violation_count: 0
```

Execution flags:

```text
environment_rollout_started: true
measured_rollout_started: true
policy_action_executed: true
training_started: false
replay_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
profile_specific_tuning: false
controller_family_ranking_claim_made: false
paper_level_claim_made: false
level3_self_id_claim_made: false
```

## Raw Diagnostic Aggregates

The repaired variant aggregate is present at:

```text
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/repair_variant_aggregate.csv
```

Raw variant-level rates are:

```text
finish_extended:
  success_obstacle_pass_rate: 0.0
  collision_failure_rate: 0.1822916667
  off_track_noncollision_noncompletion_rate: 0.8177083333

original:
  success_obstacle_pass_rate: 0.0
  collision_failure_rate: 0.1666666667
  off_track_noncollision_noncompletion_rate: 0.8333333333

road_relaxed:
  success_obstacle_pass_rate: 0.0
  collision_failure_rate: 0.1875
  off_track_noncollision_noncompletion_rate: 0.8125

road_relaxed_finish_extended:
  success_obstacle_pass_rate: 0.0
  collision_failure_rate: 0.2135416667
  off_track_noncollision_noncompletion_rate: 0.7864583333

semantics_only:
  success_obstacle_pass_rate: 0.0
  collision_failure_rate: 0.1666666667
  off_track_noncollision_noncompletion_rate: 0.8333333333
```

These are raw diagnostics only. They do not rank controller families or support
a repaired task-quality conclusion before M1896 audit.

## Artifacts

Key outputs:

```text
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/summary.json
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/episode_rows.csv
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/rollout_episode_rows.csv
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/import_episode_rows.csv
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/failure_rows.csv
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/import_failure_rows.csv
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/repair_variant_aggregate.csv
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/execution_row_kind_aggregate.csv
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/metric_completeness_summary.csv
runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/metric_completeness_failures.csv
```

The CSV line counts include headers:

```text
episode_rows.csv: 961
rollout_episode_rows.csv: 577
import_episode_rows.csv: 385
failure_rows.csv: 1
import_failure_rows.csv: 1
```

## Claim Boundary

Supported by M1895:

```text
the exact repaired bounded-smoke public diagnostic workload executed successfully
the 960-row combined panel exists with complete metrics and clean guardrails
M1896 result audit is admissible
```

Not supported by M1895:

```text
controller-family ranking
repaired task-quality conclusion
policy improvement claim
paper-level benchmark evidence
current-response / finite-window / GRU verdict
level3 self-identification evidence
```

## Decision

M1895 passes as measured execution and routes to M1896 result audit. Do not
interpret the raw aggregates as controller ranking before that audit.
