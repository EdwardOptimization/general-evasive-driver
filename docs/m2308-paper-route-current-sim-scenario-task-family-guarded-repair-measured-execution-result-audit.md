# M2308 Paper-Route Current-Sim Scenario Task-Family Guarded-Repair Measured Execution Result Audit

- status: completed
- decision: `guarded_repair_measured_execution_audit_route_to_target_guardrail_slice_diagnosis`
- manifest: `experiments/manifests/m2308-paper-route-current-sim-scenario-task-family-guarded-repair-measured-execution-result-audit.json`
- parent result: `runs/m2307_paper_route_current_sim_scenario_task_family_guarded_repair_measured_execution/summary.json`

## Completeness Audit

M2307 is a clean measured-execution artifact:

```text
result_class: current_sim_scenario_task_family_measured_execution_pass
episode_count: 1080
scenario_spec_count: 72
selected_checkpoint_count: 15
failure_count: 0
metadata_missing_count: 0
metric_completeness_failure_count: 0
guardrail_violation_count: 0
ranking_admissible_count: 0
winner_selected: false
```

Claim guardrails held:

```text
training_started: false
ppo_used: false
replay_started: false
controller_family_ranking_claim_made: false
paper_level_claim_made: false
finite_window_vs_gru_conclusion_made: false
level3_self_id_claim_made: false
```

## Global Outcome Audit

M2307 does not improve the global M2293 reference outcome:

| metric | M2293 | M2307 | delta |
| --- | ---: | ---: | ---: |
| success_count | `69` | `68` | `-1` |
| offtrack_count | `785` | `786` | `+1` |
| collision_count | `209` | `218` | `+9` |
| max_step_noncompletion_count | `7` | `4` | `-3` |
| other_failure_count | `10` | `4` | `-6` |
| mean_min_clearance_margin | `6.802372` | `6.461207` | `-0.341165` |

The M2298 repair gate required global offtrack reduction and global collision
non-increase. M2307 violates both global directions:

```text
global_offtrack_delta: +1
global_collision_delta: +9
```

This blocks any repair-success, ranking, promotion, or paper-route claim.

## Slice Preview

A temporary row-level audit over the M2298 target/guardrail spec indicates that
the failure is not only global:

```text
offtrack target slices with non-increase: 9/20
offtrack target slices with increase: 11/20
collision guardrail slices with non-increase: 4/11
collision guardrail slices with increase: 7/11
```

Notable violations include:

```text
offtrack target:
  early_far: +10
  mid: +5
  R0_stable_avoidable: +4
  aeb_feasible: +4
  left_offset: +4
  right_offset: +4
  nominal: +4

collision guardrail:
  late_close: +15
  centerline: +10
  low_mu: +8
  drift_required: +4
  right_offset: +3
  collision_failure: +9
  obstacle_collision: +9
```

This preview is enough to block direct success interpretation, but the full
31-row slice delta table should be materialized as an artifact before branch
synthesis or a repair route. Otherwise the next decision would depend on a
temporary terminal calculation.

## Route Decision

Route to:

```text
m2309-paper-route-current-sim-scenario-task-family-guarded-repair-target-guardrail-slice-diagnosis-implementation
```

M2309 should implement and run an artifact-only diagnosis that consumes:

```text
baseline episode rows:
  runs/m2293_paper_route_current_sim_scenario_task_family_measured_execution/episode_rows.csv

candidate episode rows:
  runs/m2307_paper_route_current_sim_scenario_task_family_guarded_repair_measured_execution/episode_rows.csv

repair gate spec:
  runs/m2298_paper_route_current_sim_scenario_task_family_offtrack_primary_collision_guardrail/repair_gate_spec.json
```

and writes:

```text
runs/m2309_paper_route_current_sim_scenario_task_family_guarded_repair_slice_diagnosis/summary.json
runs/m2309_paper_route_current_sim_scenario_task_family_guarded_repair_slice_diagnosis/slice_delta_rows.csv
```

M2309 must not rerun measured execution, train, rank profiles, select a winner,
or make paper/self-ID claims.

## Blocked Routes

Blocked for now:

```text
another guarded-v2 training run
profile ranking from M2307 aggregates
claiming candidate-selection improvement as repair success
claiming global return improvement as repair success
controller-family ranking
winner selection
finite-window-vs-GRU conclusion
paper-level result
level3 self-identification claim
```

## Next

Pre-register:

```text
m2309-paper-route-current-sim-scenario-task-family-guarded-repair-target-guardrail-slice-diagnosis-implementation
```
