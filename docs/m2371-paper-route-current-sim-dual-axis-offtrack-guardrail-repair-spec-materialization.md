# M2371 Paper-Route Current-Sim Dual-Axis Offtrack Guardrail Repair Spec Materialization

- status: completed
- result_class: `current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization_pass`
- manifest: `experiments/manifests/m2371-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-spec-materialization.json`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization.py`
- focused tests: `2 passed`
- source summary: `runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation/summary.json`
- output summary: `runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/summary.json`
- reset/rollout/measured execution in M2371: `false`
- policy action executed in M2371: `false`
- repair execution/training/replay/PPO: `false`
- ranking/winner/paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair claims: `false`

## Command

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

## Result

```text
source_offtrack_row_count: 54
source_collision_guardrail_row_count: 28
source_r4_row_count: 48
source_diagnostic_guardrail_row_count: 190
repair_spec_row_count: 320
ordinary_offtrack_repair_spec_count: 36
mixed_guarded_repair_spec_count: 18
collision_guardrail_spec_count: 28
r4_guardrail_spec_count: 48
diagnostic_guardrail_spec_count: 190
profile_or_pack_repair_spec_count: 0
r4_ordinary_repair_spec_count: 0
collision_blind_mixed_repair_spec_count: 0
ranking_admissible_count: 0
winner_selected_count: 0
guardrail_violation_count: 0
```

Repair family counts:

```text
priority_offtrack_containment_repair: 26
offtrack_containment_repair: 10
guarded_offtrack_containment_repair: 18
collision_guardrail_constraint: 28
r4_mitigation_semantics_guardrail: 48
diagnostic_no_ranking_guardrail: 190
```

Priority tier counts:

```text
P0: 26
P1: 28
G0: 28
R4: 48
D0: 190
```

## Guardrails

M2371 only materializes specs. It does not execute any repair lever.

Blocked repair levers are written into every spec:

```text
actor_input_change
hidden_oracle_feature_injection
profile_specific_tuning
winner_selection
r4_ordinary_avoidance_repair
collision_blind_offtrack_objective
scenario_redesign_executed_claim
training_repair_success_claim
```

Mixed guarded specs all include:

```text
collision_guardrail_required: true
guardrail_metric: collision_rate_not_worse
allowed_repair_levers includes collision_guardrail_weight
```

## Artifacts

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

## Claim Boundary

M2371 may claim only:

```text
M2368 target and guardrail rows have been materialized into repair-spec
artifacts.
```

Still blocked:

```text
repair execution
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

Pre-registered follow-up:

```text
m2372-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-spec-result-audit
```
