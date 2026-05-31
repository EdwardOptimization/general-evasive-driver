# M2068 Paper-Route Outcome-Supported Decisive Reset Materialization Repair Design

- status: completed
- decision: `outcome_supported_decisive_reset_materialization_repair_design_route_through_synthesis`
- parent audit: `docs/m2067-paper-route-outcome-supported-decisive-reset-validation-result-audit.md`
- reset/rollout/measured execution in M2068: `false`
- policy actions executed in M2068: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Goal

M2068 designs a bounded repair for the M2063 executable specs after M2066
failed reset validation `240/240`.

The repair is still no-rollout and no-reset. It should produce a repaired
materialization artifact, then route to audit before any reset validation rerun.

Two failure classes must both be addressed:

```text
zero_step_warmup_gate_schema_invalid: 117
obstacle_filter_unsampleable: 123
```

## Repair Axis 1: Warmup-Gate Schema Normalization

Problem:

```text
WarmupGateConfig rejects max_active_steps <= 0.
M2063 serialized zero-step warmup gates in both disabled and active cases.
```

Repair rule:

```text
if warmup_mode == none:
  warmup_gate.enabled = false
  warmup_gate.reveal_step = max(0, existing reveal step)
  warmup_gate.max_active_steps = positive default from base profile or 64

if warmup_mode != none:
  warmup_gate.enabled = true
  warmup_gate.reveal_step = max(0, configured reveal/diagnostic step)
  warmup_gate.max_active_steps = max(1, round(max(warmup_duration_seconds, 0.5) / dt))
```

This intentionally removes the family-only activation rule used by M2063. A
family label alone must not create an active warmup gate when the candidate's
`warmup_mode` is `none`.

The repair must preserve the candidate metadata fields:

```text
warmup_mode
warmup_duration_seconds
obstacle_reveal_delay_seconds
recent_window_seconds
older_history_offset_seconds
diagnostic_delay_seconds
task_role_semantics
```

and add repair audit fields rather than rewriting history:

```text
warmup_gate_repaired
warmup_gate_repair_reason
original_warmup_gate_enabled
original_warmup_gate_max_active_steps
repaired_warmup_gate_enabled
repaired_warmup_gate_max_active_steps
```

## Repair Axis 2: Obstacle Source/Filter Feasibility

Problem:

```text
123 specs cannot sample an obstacle scenario matching configured filters.
```

This must not be repaired by weakening paper claim guards or by accepting
arbitrary generated tasks as paper-valid. The rows remain smoke proxies.

Repair rule:

```text
for each spec, run a deterministic no-reset scenario-filter feasibility scan
using classify_obstacle_scenario over the configured speed/mu, distance, and
half-width bands.

if the existing obstacle filter has at least one accepted point:
  keep the existing obstacle distance and half-width ranges.

if the existing obstacle filter has no accepted point:
  retarget only obstacle.distance_range and obstacle.half_width_range to a
  narrow window around the nearest accepted AEB-infeasible scenario candidate
  for the same family/difficulty intent.
```

Accepted means:

```text
scenario label is in allowed_labels
require_aeb_infeasible is satisfied
threshold-score constraint is satisfied or explicitly recorded as repaired
time-after-friction-step constraint is satisfied when applicable
```

The implementation should write audit fields:

```text
obstacle_filter_repaired
obstacle_filter_repair_reason
original_obstacle_distance_range
original_obstacle_half_width_range
repaired_obstacle_distance_range
repaired_obstacle_half_width_range
scenario_filter_feasible_before
scenario_filter_feasible_after
scenario_filter_candidate_label
scenario_filter_candidate_score
original_obstacle_max_threshold_score
repaired_obstacle_max_threshold_score
```

The repair may broaden or retarget smoke-proxy geometry, but it must not:

```text
change actor inputs;
change reward or dynamics;
run env reset;
run rollout;
execute policy actions;
rank controller families;
mark generated rows as paper-valid.
```

## M2070 Command Route After Synthesis

The branch has reached its workflow synthesis cadence. M2069 must synthesize the
branch first. If that synthesis decision is `continue`, M2070 should implement
and run:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_outcome_supported_decisive_reset_materialization_repair_preflight.py

PYTHONPATH=src python -m autodrift.paper_route_outcome_supported_decisive_reset_materialization_repair_preflight \
  --executable-task-specs runs/m2063_paper_route_outcome_supported_decisive_materialization_preflight/executable_task_specs.json \
  --reset-failure-rows runs/m2066_paper_route_outcome_supported_decisive_reset_validation_preflight/reset_failure_rows.csv \
  --profile-run-dir runs/m1674_controller_family_one_seed_public_pilot \
  --output-dir runs/m2070_paper_route_outcome_supported_decisive_reset_materialization_repair_preflight \
  --next-blocker m2071-paper-route-outcome-supported-decisive-reset-materialization-repair-result-audit
```

M2070 should write:

```text
runs/m2070_paper_route_outcome_supported_decisive_reset_materialization_repair_preflight/summary.json
runs/m2070_paper_route_outcome_supported_decisive_reset_materialization_repair_preflight/repaired_executable_task_specs.json
runs/m2070_paper_route_outcome_supported_decisive_reset_materialization_repair_preflight/repaired_executable_task_specs.csv
runs/m2070_paper_route_outcome_supported_decisive_reset_materialization_repair_preflight/repair_rows.csv
runs/m2070_paper_route_outcome_supported_decisive_reset_materialization_repair_preflight/planned_sentinel_workload.csv
runs/m2070_paper_route_outcome_supported_decisive_reset_materialization_repair_preflight/profile_artifacts.csv
runs/m2070_paper_route_outcome_supported_decisive_reset_materialization_repair_preflight/claim_boundary.csv
```

## M2070 Pass Gates

M2070 passes only if:

```text
input_executable_spec_count == 240
repaired_executable_spec_count == 240
planned_sentinel_workload_count == 1200
sentinel_profile_count == 5
zero_step_warmup_gate_invalid_count_after == 0
scenario_filter_feasible_after_count == 240
scenario_filter_infeasible_after_count == 0
warmup_gate_repaired_count >= 117
obstacle_filter_repaired_count >= 123
family_quota_pass == true
split_quota_pass == true
difficulty_axis_coverage_pass == true
contract_violation_count == 0
forbidden_key_violation_count == 0
metadata_missing_count == 0
guardrail_violation_count == 0
environment_reset_started == false
environment_rollout_started == false
policy_action_executed == false
measured_rollout_started == false
training_started == false
replay_started == false
ppo_used == false
promoted == false
private_holdout_used == false
actor_input_contract_changed == false
profile_specific_tuning == false
controller_family_ranking_claim_made == false
paper_level_claim_made == false
finite_window_vs_gru_conclusion_made == false
level3_self_id_claim_made == false
```

If M2070 passes, M2071 must audit the repaired materialization before any reset
validation rerun. If M2070 fails, M2071 should classify which repair axis remains
invalid rather than weakening claim guards.

## Supported Claims

M2068 supports only this process claim:

```text
the next repair should be a combined no-rollout materialization repair with
explicit warmup-gate and obstacle-filter axes.
```

Unsupported:

```text
reset validity;
measured execution readiness;
controller-family ranking;
paper-level benchmark evidence;
finite-window-vs-GRU conclusion;
level3 self-identification.
```

## Next

Next milestone:

```text
m2069-paper-route-outcome-supported-decisive-task-distribution-synthesis
```
