# M2375 Paper-Route Current-Sim Dual-Axis Offtrack Guardrail Repair Plan Materialization

- status: completed
- result_class: `current_sim_dual_axis_offtrack_guardrail_repair_plan_materialization_pass`
- manifest: `experiments/manifests/m2375-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-plan-materialization.json`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_offtrack_guardrail_repair_plan_materialization.py`
- focused tests: `2 passed`
- source summary: `runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/summary.json`
- output summary: `runs/m2375_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_plan_materialization/summary.json`
- reset/rollout/measured execution in M2375: `false`
- policy action executed in M2375: `false`
- repair execution/training/replay/PPO: `false`
- ranking/winner/paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Command

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_dual_axis_offtrack_guardrail_repair_plan_materialization \
  --summary runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/summary.json \
  --repair-spec-rows runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/repair_spec_rows.csv \
  --ordinary-rows runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/ordinary_offtrack_repair_spec_rows.csv \
  --mixed-rows runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/mixed_guarded_repair_spec_rows.csv \
  --collision-rows runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/collision_guardrail_spec_rows.csv \
  --r4-rows runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/r4_guardrail_spec_rows.csv \
  --diagnostic-rows runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/diagnostic_guardrail_spec_rows.csv \
  --output-dir runs/m2375_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_plan_materialization \
  --next-blocker m2376-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-plan-materialization-result-audit
```

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_plan_materialization.py
```

## Result

```text
input_repair_spec_row_count: 320
ordinary_offtrack_source_count: 36
mixed_guarded_source_count: 18
collision_guardrail_source_count: 28
r4_guardrail_source_count: 48
diagnostic_guardrail_source_count: 190
reward_delta_row_count: 54
curriculum_weight_row_count: 54
guardrail_constraint_row_count: 284
target_guardrail_constraint_min_count: 266
mixed_guarded_constraint_row_count: 18
claim_boundary_row_count: 10
profile_specific_tuning_count: 0
actor_input_change_count: 0
hidden_oracle_feature_injection_count: 0
collision_blind_mixed_repair_count: 0
r4_ordinary_repair_count: 0
ranking_admissible_count: 0
winner_selected_count: 0
guardrail_violation_count: 0
```

Constraint family counts:

```text
collision: 46
r4_mitigation_semantics: 48
diagnostic_no_ranking: 190
```

The 46 collision constraints include:

```text
28 collision-only guardrail specs
18 mixed guarded offtrack specs
```

## Artifacts

```text
runs/m2375_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_plan_materialization/summary.json
runs/m2375_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_plan_materialization/repair_implementation_plan.json
runs/m2375_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_plan_materialization/reward_delta_rows.csv
runs/m2375_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_plan_materialization/curriculum_weight_rows.csv
runs/m2375_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_plan_materialization/guardrail_constraint_rows.csv
runs/m2375_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_plan_materialization/mixed_guarded_constraint_rows.csv
runs/m2375_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_plan_materialization/claim_boundary.csv
```

## Guardrails

M2375 only materializes plan artifacts. It does not execute repair levers.

Blocked levers in the plan:

```text
actor_input_change
hidden_oracle_feature_injection
profile_specific_tuning
support_policy_ranking
controller_family_ranking
winner_selection
active_scenario_config_overwrite
r4_ordinary_avoidance_repair
collision_blind_offtrack_objective
scenario_redesign_executed_claim
training_repair_success_claim
```

Runtime and claim flags are all false:

```text
environment_reset_started: false
environment_rollout_started: false
policy_action_executed: false
measured_rollout_started: false
repair_execution_started: false
training_started: false
replay_started: false
ppo_used: false
active_config_overwritten: false
paper_level_claim_made: false
finite_window_vs_gru_conclusion_made: false
level3_self_id_claim_made: false
scenario_redesign_executed_claim_made: false
training_repair_success_claim_made: false
current_sim_verdict_claim_made: false
```

## Claim Boundary

M2375 may claim only:

```text
M2371 repair specs and M2373 implementation design have been materialized into
artifact-only repair-plan files.
```

Still blocked:

```text
repair execution
training repair success
scenario redesign executed
controller-family ranking
support-policy ranking
winner selection
paper-level benchmark evidence
finite-window vs GRU conclusion
level3 self-identification evidence
current-sim verdict
```

## Next

Pre-registered follow-up:

```text
m2376-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-plan-materialization-result-audit
```
