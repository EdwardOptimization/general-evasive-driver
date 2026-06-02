# M2370 Paper-Route Current-Sim Dual-Axis Offtrack Guardrail Repair Design

- status: completed
- decision: `offtrack_guardrail_repair_design_admit_artifact_only_repair_spec_materializer`
- manifest: `experiments/manifests/m2370-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-design.json`
- parent audit: `docs/m2369-paper-route-current-sim-dual-axis-actionable-target-consolidation-result-audit.md`
- reset/rollout/measured execution in M2370: `false`
- policy action executed in M2370: `false`
- training/replay/PPO: `false`
- ranking/winner/paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair claims: `false`

## Design Goal

M2370 designs an artifact-only repair-spec materializer from M2368 consolidated
artifacts:

```text
offtrack repair target rows:
  runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation/offtrack_repair_target_rows.csv

collision guardrail rows:
  runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation/collision_guardrail_rows.csv

R4 mitigation semantics rows:
  runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation/r4_mitigation_semantics_rows.csv

diagnostic guardrail rows:
  runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation/diagnostic_guardrail_rows.csv
```

It does not change reward code, scenario config, actor inputs, training, or
evaluation. It only defines how the next materializer should turn the
consolidated rows into repair-spec rows.

## Repair Families

M2371 should assign one repair family per source row:

```text
priority_offtrack_containment_repair:
  ordinary offtrack target with is_high_priority_offtrack true.

offtrack_containment_repair:
  ordinary offtrack target without collision_guardrail_required.

guarded_offtrack_containment_repair:
  offtrack target with collision_guardrail_required true.

collision_guardrail_constraint:
  collision guardrail row that is not an ordinary offtrack repair target.

r4_mitigation_semantics_guardrail:
  R4 mitigation semantics row, never ordinary repair.

diagnostic_no_ranking_guardrail:
  diagnostic/global/pack/profile/sampling row, never ordinary repair.
```

## Allowed Repair Levers

Repair specs may name these levers for later design, but M2371 must not execute
them:

```text
offtrack_margin_reward:
  increase sensitivity to road-boundary margin and offtrack overshoot.

recovery_window_reward:
  reward return to bounded road corridor after near-limit maneuver.

boundary_overshoot_penalty:
  penalize severity of offtrack overshoot rather than only terminal event.

curriculum_sampling_weight:
  increase sampling probability of consolidated target categories.

collision_guardrail_weight:
  preserve collision rate on mixed and collision-only guardrail slices.

r4_mitigation_metric_guard:
  keep unavoidable mitigation semantics separate from ordinary avoidance.
```

Blocked levers:

```text
actor input change
hidden/oracle feature injection
profile-specific tuning
pack/profile winner selection
R4 ordinary avoidance repair
collision-blind offtrack objective
scenario redesign executed claim
training repair success claim
```

## Metrics

Each repair spec should carry intended metrics:

```text
target_metric:
  offtrack_rate_down

guardrail_metric:
  collision_rate_not_worse

R4 metric:
  mitigation_semantics_preserved

diagnostic metric:
  no_ranking_no_winner_claims
```

For mixed offtrack/collision rows, both target and guardrail metrics apply.

## Expected Materializer Outputs

M2371 should write:

```text
runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/summary.json
runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/repair_spec_rows.csv
runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/ordinary_offtrack_repair_spec_rows.csv
runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/mixed_guarded_repair_spec_rows.csv
runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/collision_guardrail_spec_rows.csv
runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/r4_guardrail_spec_rows.csv
runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/diagnostic_guardrail_spec_rows.csv
runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/claim_boundary.csv
```

## Frozen M2371 Command

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization \
  --summary runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation/summary.json \
  --offtrack-target-rows runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation/offtrack_repair_target_rows.csv \
  --collision-guardrail-rows runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation/collision_guardrail_rows.csv \
  --r4-rows runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation/r4_mitigation_semantics_rows.csv \
  --diagnostic-guardrail-rows runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation/diagnostic_guardrail_rows.csv \
  --output-dir runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization \
  --target-offtrack-row-count 54 \
  --target-collision-guardrail-row-count 28 \
  --target-r4-row-count 48 \
  --target-diagnostic-guardrail-row-count 190 \
  --next-blocker m2372-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-spec-result-audit
```

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization.py
```

## Pass Gates

M2371 passes only if:

```text
source_offtrack_row_count == 54
source_collision_guardrail_row_count == 28
source_r4_row_count == 48
source_diagnostic_guardrail_row_count == 190
repair_spec_row_count > 0
ordinary_offtrack_repair_spec_count > 0
mixed_guarded_repair_spec_count > 0
collision_guardrail_spec_count > 0
r4_guardrail_spec_count > 0
diagnostic_guardrail_spec_count > 0
profile_or_pack_repair_spec_count == 0
r4_ordinary_repair_spec_count == 0
collision_blind_mixed_repair_spec_count == 0
ranking_admissible_count == 0
winner_selected_count == 0
guardrail_violation_count == 0
environment_rollout_started == false
policy_action_executed == false
measured_rollout_started == false
training_started == false
replay_started == false
ppo_used == false
paper_level_claim_made == false
finite_window_vs_gru_conclusion_made == false
level3_self_id_claim_made == false
scenario_redesign_executed_claim_made == false
training_repair_success_claim_made == false
```

## Claim Boundary

M2370 may claim only:

```text
artifact-only offtrack guardrail repair-spec design.
```

Still blocked:

```text
controller-family ranking
support-policy ranking
winner selection
paper-level benchmark evidence
finite-window vs GRU conclusion
level3 self-identification evidence
scenario redesign executed
training repair success
```

## Next

Pre-register:

```text
m2371-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-spec-materialization
```
