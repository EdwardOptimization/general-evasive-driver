# M2336 Paper-Route Current-Sim Role-Stratified Residual Support Rescore Implementation

- status: completed
- result_class: `current_sim_role_stratified_residual_support_rescore_pass`
- manifest: `experiments/manifests/m2336-paper-route-current-sim-role-stratified-residual-support-rescore-implementation.json`
- implementation: `src/autodrift/paper_route_current_sim_role_stratified_residual_support_rescore.py`
- tests: `tests/test_paper_route_current_sim_role_stratified_residual_support_rescore.py`
- summary: `runs/m2336_paper_route_current_sim_role_stratified_residual_support_rescore/summary.json`
- reset/rollout/policy action: `false`
- measured execution: `false`
- training/replay/PPO: `false`
- support-policy ranking claim made: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Command

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_role_stratified_residual_support_rescore \
  --residual-dir runs/m2321_paper_route_current_sim_scenario_task_family_residual_support_audit \
  --role-redesign-dir runs/m2324_paper_route_current_sim_scenario_task_family_role_stratified_residual_redesign \
  --r4-semantics-dir runs/m2333_paper_route_current_sim_r4_mitigation_metric_semantics \
  --output-dir runs/m2336_paper_route_current_sim_role_stratified_residual_support_rescore \
  --target-residual-scenario-count 48 \
  --next-blocker m2337-paper-route-current-sim-role-stratified-residual-support-rescore-result-audit
```

## Implementation

M2336 implements the artifact-only rescore from M2335. It reads existing
residual and R4 semantics artifacts and writes:

```text
runs/m2336_paper_route_current_sim_role_stratified_residual_support_rescore/residual_rescore_rows.csv
runs/m2336_paper_route_current_sim_role_stratified_residual_support_rescore/role_rescore_summary.csv
runs/m2336_paper_route_current_sim_role_stratified_residual_support_rescore/route_rescore_summary.csv
runs/m2336_paper_route_current_sim_role_stratified_residual_support_rescore/claim_boundary.csv
runs/m2336_paper_route_current_sim_role_stratified_residual_support_rescore/summary.json
```

The script does not run the environment or execute policies.

## Summary

```text
input_residual_scenario_count: 48
rescored_residual_scenario_count: 48
role_summary_count: 4
route_summary_count: 4
r0_residual_count: 0
r1_residual_count: 0
r4_proxy_semantics_post_collision_blocked_count: 12
support_policy_coverage_gap_count: 23
scenario_or_support_redesign_gap_count: 12
metric_semantics_edge_count: 1
unclassified_residual_route_count: 0
ranking_admissible_count: 0
winner_selected_count: 0
guardrail_violation_count: 0
```

## Route Summary

```text
support_policy_coverage_gap: 23
scenario_or_support_redesign_gap: 12
r4_proxy_metric_semantics_available_post_collision_blocked: 12
metric_semantics_edge_case: 1
```

Role summary:

```text
R2_handling_limit_drift_capable_avoidance:
  support_policy_coverage_gap: 7
  scenario_or_support_redesign_gap: 5

R3_recovery_after_limit:
  support_policy_coverage_gap: 8
  scenario_or_support_redesign_gap: 3
  metric_semantics_edge_case: 1

R4_unavoidable_mitigation:
  r4_proxy_metric_semantics_available_post_collision_blocked: 12

R5_hidden_dynamics_robustness:
  support_policy_coverage_gap: 8
  scenario_or_support_redesign_gap: 4
```

## Interpretation

M2336 updates the stale M2321/M2324 residual map:

```text
R4 is no longer a field-export gap for impact proxies.
R4 remains blocked for post-collision mitigation semantics.
R2/R3/R5 remain split between support-policy coverage and scenario/support redesign.
One metric edge remains.
```

This is still not a controller comparison or residual-solved claim. It only
gives the next audit a cleaner residual route map.

## Verification

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_current_sim_role_stratified_residual_support_rescore.py
```

Result:

```text
1 passed in 0.11s
```

## Follow-Up Manifest

```text
experiments/manifests/m2337-paper-route-current-sim-role-stratified-residual-support-rescore-result-audit.json
```

Next route:

```text
m2337-paper-route-current-sim-role-stratified-residual-support-rescore-result-audit
```
