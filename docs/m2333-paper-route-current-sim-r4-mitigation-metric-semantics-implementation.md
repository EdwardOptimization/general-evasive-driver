# M2333 Paper-Route Current-Sim R4 Mitigation Metric Semantics Implementation

- status: completed
- result_class: `current_sim_r4_mitigation_metric_semantics_audit_pass`
- manifest: `experiments/manifests/m2333-paper-route-current-sim-r4-mitigation-metric-semantics-implementation.json`
- implementation: `src/autodrift/paper_route_current_sim_r4_mitigation_metric_semantics_audit.py`
- tests: `tests/test_paper_route_current_sim_r4_mitigation_metric_semantics_audit.py`
- summary: `runs/m2333_paper_route_current_sim_r4_mitigation_metric_semantics/summary.json`
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
PYTHONPATH=src python -m autodrift.paper_route_current_sim_r4_mitigation_metric_semantics_audit \
  --input-dir runs/m2330_paper_route_current_sim_r4_metric_instrumented_support_diagnostic_rerun \
  --output-dir runs/m2333_paper_route_current_sim_r4_mitigation_metric_semantics \
  --target-scenario-count 12 \
  --next-blocker m2334-paper-route-current-sim-r4-mitigation-metric-semantics-result-audit
```

## Implementation

M2333 implements the artifact-only semantics audit designed by M2332. It reads
only M2330 CSV artifacts and writes:

```text
runs/m2333_paper_route_current_sim_r4_mitigation_metric_semantics/r4_metric_semantics_rows.csv
runs/m2333_paper_route_current_sim_r4_mitigation_metric_semantics/r4_metric_proxy_policy_aggregate.csv
runs/m2333_paper_route_current_sim_r4_mitigation_metric_semantics/r4_claim_boundary.csv
runs/m2333_paper_route_current_sim_r4_mitigation_metric_semantics/summary.json
```

The implementation does not import or instantiate the environment, execute
policies, train, replay, PPO, promote, or rank controller/support policies.

## Summary

```text
scenario_count: 12 / 12
episode_count: 180
policy_aggregate_count: 3
impact_proxy_available_scenario_count: 12
post_collision_blocked_scenario_count: 12
obstacle_passage_success_insufficient_count: 12
ranking_admissible_count: 0
winner_selected_count: 0
paper_level_claim_count: 0
level3_self_id_claim_count: 0
guardrail_violation_count: 0
```

All 12 R4 scenarios have:

```text
obstacle_passage_success_semantics: insufficient_for_r4
impact_proxy_semantics: available
post_collision_semantics: blocked_current_sim_collision_terminates
r4_metric_semantics_status: proxy_metric_available_post_collision_blocked
comparison_admissibility: descriptive_proxy_audit_only
```

## Scenario Semantics

`r4_metric_semantics_rows.csv` records one row per R4 scenario. The rows
preserve M2330 support labels while adding R4-specific semantics:

```text
support_mixed: 3
support_blocked: 9
proxy_metric_available_post_collision_blocked: 12
descriptive_proxy_audit_only: 12
ranking_admissible true: 0
winner_selected true: 0
```

The result means current-sim R4 diagnostics are usable for descriptive
impact-proxy semantics, but not for final post-collision mitigation-performance
claims.

## Policy Aggregate Boundary

`r4_metric_proxy_policy_aggregate.csv` preserves per-support-policy descriptive
aggregates without ranking:

```text
aeb:
  episode_count: 60
  collision_count: 59
  offtrack_count: 1
  impact_proxy_available_count: 59
  impact_speed_mps_mean: 15.066808872218932
  collision_mitigation_score_mean: 15.776193809417634

aes:
  episode_count: 60
  collision_count: 58
  offtrack_count: 1
  impact_proxy_available_count: 58
  impact_speed_mps_mean: 13.623987417835046
  collision_mitigation_score_mean: 14.163401872742776

envelope_aes:
  episode_count: 60
  collision_count: 56
  offtrack_count: 4
  impact_proxy_available_count: 56
  impact_speed_mps_mean: 16.161697154698228
  collision_mitigation_score_mean: 15.80956853098948
```

Every policy aggregate row keeps:

```text
ranking_admissible: false
winner_selected: false
paper_level_claim_made: false
level3_self_id_claim_made: false
```

These numbers are descriptive diagnostics only.

## Claim Boundary

`r4_claim_boundary.csv` explicitly allows only:

```text
artifact_only_r4_metric_semantics
```

and blocks:

```text
support_policy_ranking
paper_level_mitigation_performance
post_collision_recovery_measured
level3_self_identification
```

## Verification

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_current_sim_r4_mitigation_metric_semantics_audit.py
```

Result:

```text
1 passed in 0.11s
```

## Follow-Up Manifest

```text
experiments/manifests/m2334-paper-route-current-sim-r4-mitigation-metric-semantics-result-audit.json
```

Next route:

```text
m2334-paper-route-current-sim-r4-mitigation-metric-semantics-result-audit
```
