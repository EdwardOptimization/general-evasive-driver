# M2335 Paper-Route Current-Sim Role-Stratified Residual Support Rescore Design

- status: completed
- result_class: `role_stratified_residual_support_rescore_design_admit_artifact_only_implementation`
- manifest: `experiments/manifests/m2335-paper-route-current-sim-role-stratified-residual-support-rescore-design.json`
- parent audit: `docs/m2334-paper-route-current-sim-r4-mitigation-metric-semantics-result-audit.md`
- reset/rollout/policy action in M2335: `false`
- measured execution in M2335: `false`
- training/replay/PPO: `false`
- support-policy ranking claim made: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Design Purpose

M2335 designs an artifact-only residual support rescore after two role-semantics
repairs:

```text
R0 safe-stop semantics:
  repaired in M2318

R4 unavoidable mitigation semantics:
  impact-proxy semantics materialized in M2333
  post-collision canonical semantics remain blocked
```

The goal is to update the stale residual map from M2321/M2324 before any
controller comparison resumes.

## Inputs

M2336 should read only existing artifacts:

```text
runs/m2321_paper_route_current_sim_scenario_task_family_residual_support_audit/residual_scenario_rows.csv
runs/m2321_paper_route_current_sim_scenario_task_family_residual_support_audit/summary.json
runs/m2324_paper_route_current_sim_scenario_task_family_role_stratified_residual_redesign/role_stratified_residual_rows.csv
runs/m2324_paper_route_current_sim_scenario_task_family_role_stratified_residual_redesign/r2_r3_r5_coverage_redesign_rows.csv
runs/m2324_paper_route_current_sim_scenario_task_family_role_stratified_residual_redesign/summary.json
runs/m2333_paper_route_current_sim_r4_mitigation_metric_semantics/r4_metric_semantics_rows.csv
runs/m2333_paper_route_current_sim_r4_mitigation_metric_semantics/summary.json
```

M2336 must not run reset, rollout, measured execution, training, replay, PPO,
ranking, promotion, or private holdout.

## Rescore Rules

### R0/R1

M2321 already reports:

```text
r0_residual_count: 0
r1_residual_count: 0
```

M2336 should preserve this as:

```text
role_semantics_resolved_no_residual
```

No new rows are required for R0/R1 unless the input artifacts unexpectedly
contain residual rows.

### R4

For each R4 residual row, join by `scenario_spec_id` against:

```text
runs/m2333_paper_route_current_sim_r4_mitigation_metric_semantics/r4_metric_semantics_rows.csv
```

If:

```text
r4_metric_semantics_status == proxy_metric_available_post_collision_blocked
```

then rescore to:

```text
rescore_route_label:
  r4_proxy_metric_semantics_available_post_collision_blocked

rescore_category:
  role_semantics_proxy_available_current_sim_limited

requires_post_collision_continuation:
  true

requires_new_rollout:
  false

comparison_admissibility:
  blocked_until_rescore_audited
```

This means the old M2324 `r4_mitigation_metric_availability_gap` is no longer a
field/export gap for impact proxies. It remains a current-sim semantic limitation
for final post-collision mitigation.

### R2/R3/R5

For R2/R3/R5 rows, preserve the M2324 role-stratified routes:

```text
support_policy_coverage_materialization_required
  -> support_policy_coverage_gap

scenario_or_support_redesign_materialization_required
  -> scenario_or_support_redesign_gap

metric_semantics_edge_case
  -> metric_semantics_edge_case
```

M2336 should not repair these rows. It only makes the remaining route map
explicit after R0/R4 semantics are accounted for.

## Expected Counts

From current artifacts, M2336 should expect:

```text
input_residual_scenario_count: 48
R0 residual rows: 0
R1 residual rows: 0
R2/R3/R5 support coverage rows: 23
R2/R3/R5 scenario/support redesign rows: 12
metric edge rows: 1
R4 proxy-semantics/post-collision-blocked rows: 12
guardrail_violation_count: 0
```

## Proposed Outputs

M2336 should write:

```text
runs/m2336_paper_route_current_sim_role_stratified_residual_support_rescore/residual_rescore_rows.csv
runs/m2336_paper_route_current_sim_role_stratified_residual_support_rescore/role_rescore_summary.csv
runs/m2336_paper_route_current_sim_role_stratified_residual_support_rescore/route_rescore_summary.csv
runs/m2336_paper_route_current_sim_role_stratified_residual_support_rescore/claim_boundary.csv
runs/m2336_paper_route_current_sim_role_stratified_residual_support_rescore/summary.json
```

`residual_rescore_rows.csv` should include at least:

```text
scenario_spec_id
role_family
old_support_label
old_primary_route_label
old_design_route_label
rescore_route_label
rescore_category
rescore_reason
requires_artifact_only_followup
requires_new_rollout
requires_post_collision_continuation
comparison_admissibility
diagnostic_only
ranking_admissible
winner_selected
paper_level_claim_made
level3_self_id_claim_made
```

`summary.json` should report at least:

```text
input_residual_scenario_count
rescored_residual_scenario_count
r4_proxy_semantics_post_collision_blocked_count
support_policy_coverage_gap_count
scenario_or_support_redesign_gap_count
metric_semantics_edge_count
r0_residual_count
r1_residual_count
ranking_admissible_count
winner_selected_count
guardrail_violation_count
result_class
next_blocker
```

## Decision

M2335 admits artifact-only implementation:

```text
next: m2336-paper-route-current-sim-role-stratified-residual-support-rescore-implementation
```

Allowed claim:

```text
M2335 defines a bounded artifact-only role-stratified residual support rescore
after R0 and R4 semantics repairs.
```

Blocked claims:

```text
residual support solved;
controller comparison ready;
support policies ranked;
controller families ranked;
winner selected;
paper-level evidence;
finite-window vs GRU conclusion;
level3 self-identification evidence.
```

## Follow-Up Manifest

```text
experiments/manifests/m2336-paper-route-current-sim-role-stratified-residual-support-rescore-implementation.json
```
