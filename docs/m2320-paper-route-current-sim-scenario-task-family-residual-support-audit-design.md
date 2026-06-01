# M2320 Paper-Route Current-Sim Scenario Task-Family Residual Support Audit Design

- status: completed
- decision: `residual_support_audit_design_admit_artifact_only_implementation`
- manifest: `experiments/manifests/m2320-paper-route-current-sim-scenario-task-family-residual-support-audit-design.json`
- parent synthesis: `docs/m2319-paper-route-current-sim-scenario-task-family-feasibility-calibration-branch-synthesis.md`
- reset/rollout/policy action in M2320: `false`
- training/replay/PPO in M2320: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Design Goal

M2320 freezes an artifact-only residual-support audit over the repaired M2318
support labels. It should classify the remaining non-clear scenarios before any
new training, controller-family comparison, or scenario redesign.

Current repaired support structure:

```text
total scenarios: 72
support_clear: 24
support_mixed: 26
support_blocked: 21
metric_conflict: 1
residual non-clear scenarios: 48

R0: support_clear 12 / 12
R1: support_clear 12 / 12
R2: support_mixed 7 / 12, support_blocked 5 / 12
R3: support_mixed 8 / 12, support_blocked 3 / 12, metric_conflict 1 / 12
R4: support_mixed 3 / 12, support_blocked 9 / 12
R5: support_mixed 8 / 12, support_blocked 4 / 12
```

The audit should not judge the learned driver. It should answer whether the
remaining scenario/task rows are fair, supported, and semantically clear enough
to become training/evaluation targets.

## Inputs

M2321 should consume only M2318 repaired artifacts:

```text
runs/m2318_paper_route_current_sim_scenario_task_family_role_success_semantics_repair/episode_rows_rescored.csv
runs/m2318_paper_route_current_sim_scenario_task_family_role_success_semantics_repair/scenario_support_labels_rescored.csv
runs/m2318_paper_route_current_sim_scenario_task_family_role_success_semantics_repair/role_support_summary_rescored.csv
```

No reset, rollout, policy action, measured execution, training, replay, PPO, or
private holdout is allowed in M2321.

## Residual Route Labels

For each scenario with `support_label != support_clear`, M2321 should emit one
primary route label:

```text
metric_semantics_audit_candidate:
  support_label == metric_conflict

support_policy_coverage_candidate:
  support_label == support_mixed
  at least one policy has partial success but no policy reaches clear threshold

scenario_or_support_redesign_candidate:
  support_label == support_blocked
  no support policy produces enough role-success evidence

mitigation_semantics_or_support_redesign_candidate:
  role_family == R4_unavoidable_mitigation
  support_label in {support_mixed, support_blocked}
```

The R4 label is more specific because unavoidable mitigation may need different
success semantics than obstacle avoidance. It must not be treated as solved or
as ordinary failure without a mitigation metric.

## Required Groupings

M2321 should group residual scenarios by:

```text
role_family
sampled_obstacle_label
support_label
hidden_dynamics_bucket
obstacle_longitudinal_timing_bucket
obstacle_lateral_offset_bucket
primary_route_label
dominant_failure_mode
```

Dominant failure modes should be computed from M2318 rescored episode rows:

```text
success_supported
collision_dominated_failure
offtrack_dominated_failure
max_step_noncompletion_dominated_failure
mixed_failure
low_support_or_incomplete
```

Support-policy counts should remain diagnostic:

```text
aeb_success_count / collision_count / offtrack_count
aes_success_count / collision_count / offtrack_count
envelope_aes_success_count / collision_count / offtrack_count
```

These counts may explain support coverage, but they are not a ranking or winner
selection.

## Outputs

M2321 should write:

```text
summary.json
residual_scenario_rows.csv
residual_role_summary.csv
residual_axis_summary.csv
residual_route_summary.csv
residual_support_policy_summary.csv
claim_boundary.csv
run_state.json
```

The summary should include:

```text
input_scenario_count
residual_scenario_count
support_clear_count
support_mixed_count
support_blocked_count
metric_conflict_count
residual_role_count
r0_residual_count
r1_residual_count
r2_r5_residual_count
guardrail_violation_count
next_blocker
```

Expected M2321 gates:

```text
input_scenario_count == 72
residual_scenario_count == 48
support_clear_count == 24
support_mixed_count == 26
support_blocked_count == 21
metric_conflict_count == 1
r0_residual_count == 0
r1_residual_count == 0
r2_r5_residual_count == 48
guardrail_violation_count == 0
```

## Command

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_scenario_task_family_residual_support_audit \
  --episode-rows runs/m2318_paper_route_current_sim_scenario_task_family_role_success_semantics_repair/episode_rows_rescored.csv \
  --scenario-support-labels runs/m2318_paper_route_current_sim_scenario_task_family_role_success_semantics_repair/scenario_support_labels_rescored.csv \
  --role-support-summary runs/m2318_paper_route_current_sim_scenario_task_family_role_success_semantics_repair/role_support_summary_rescored.csv \
  --output-dir runs/m2321_paper_route_current_sim_scenario_task_family_residual_support_audit \
  --target-scenario-count 72 \
  --target-residual-scenario-count 48 \
  --next-blocker m2322-paper-route-current-sim-scenario-task-family-residual-support-audit-result-audit
```

## Required Tests

Focused tests should cover:

```text
support_clear rows are excluded from residual_scenario_rows;
support_mixed rows route to support_policy_coverage_candidate;
support_blocked rows route to scenario_or_support_redesign_candidate;
R4 residual rows route to mitigation_semantics_or_support_redesign_candidate;
metric_conflict rows route to metric_semantics_audit_candidate;
R0/R1 residual counts are fail-closed in summary;
support policy counts are diagnostic and do not select a winner.
```

## Claim Boundary

Allowed claim:

```text
M2320 defines an artifact-only residual-support audit over M2318 repaired
support artifacts.
```

Blocked claims:

```text
driver performance result;
training result;
controller-family or support-policy ranking;
winner selection;
paper-level current-sim evidence;
finite-window vs GRU conclusion;
level3 self-identification evidence;
residual support solved.
```

## Follow-Up

Pre-register:

```text
experiments/manifests/m2321-paper-route-current-sim-scenario-task-family-residual-support-audit-implementation.json
```
