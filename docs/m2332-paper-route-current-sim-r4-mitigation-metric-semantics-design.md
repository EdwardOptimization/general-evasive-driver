# M2332 Paper-Route Current-Sim R4 Mitigation Metric Semantics Design

- status: completed
- result_class: `r4_mitigation_metric_semantics_design_admit_artifact_only_implementation`
- manifest: `experiments/manifests/m2332-paper-route-current-sim-r4-mitigation-metric-semantics-design.json`
- parent audit: `docs/m2331-paper-route-current-sim-r4-metric-instrumented-support-diagnostic-rerun-result-audit.md`
- reset/rollout/policy action in M2332: `false`
- measured execution in M2332: `false`
- training/replay/PPO: `false`
- support-policy ranking claim made: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Design Purpose

M2332 defines bounded R4 mitigation metric semantics for the current simulator.
R4 scenarios are `R4_unavoidable_mitigation`; their role is mitigation when
avoidance is infeasible, so obstacle-passage success cannot be the only final
role-success semantic.

The design uses only existing M2330 artifacts:

```text
runs/m2330_paper_route_current_sim_r4_metric_instrumented_support_diagnostic_rerun/summary.json
runs/m2330_paper_route_current_sim_r4_metric_instrumented_support_diagnostic_rerun/episode_rows.csv
runs/m2330_paper_route_current_sim_r4_metric_instrumented_support_diagnostic_rerun/r4_metric_field_completeness.csv
runs/m2330_paper_route_current_sim_r4_metric_instrumented_support_diagnostic_rerun/scenario_support_labels.csv
runs/m2330_paper_route_current_sim_r4_metric_instrumented_support_diagnostic_rerun/role_support_summary.csv
```

M2332 does not design a controller comparison, support-policy ranking, paper
claim, finite-window vs GRU verdict, or self-identification claim.

## Semantic Split

R4 current-sim semantics are split into two layers:

```text
Layer A: available impact-proxy mitigation semantics
Layer B: unavailable post-collision canonical mitigation semantics
```

Layer A can be audited now. Layer B must remain blocked until simulator support
or diagnostic continuation exists.

## Available Impact-Proxy Fields

The following fields are available and may be used for descriptive R4
mitigation-proxy semantics:

```text
impact_speed_mps
impact_speed_mps_available
time_to_collision_s
time_to_collision_s_available
collision_side_proxy
impact_speed_proxy
impact_beta_abs
impact_yaw_rate_abs
impact_severity_proxy
collision_mitigation_score
```

Usage rules:

```text
impact_speed_mps:
  descriptive impact-speed proxy only;
  lower value may be logged as lower impact speed but must not be used to
  select a winner in this branch.

time_to_collision_s:
  descriptive timing proxy only;
  useful for severity context but not a success criterion by itself.

collision_side_proxy:
  descriptive collision-side proxy from obstacle body-frame geometry.

impact_beta_abs / impact_yaw_rate_abs:
  impact stability proxies; not driver skill proof.

impact_severity_proxy / collision_mitigation_score:
  current-sim proxy scores for artifact-only semantics;
  not a paper-level mitigation-performance metric.
```

## Unavailable Canonical Fields

The following fields remain unavailable in current collision-terminating
rollouts and must stay availability-false:

```text
delta_v_at_impact_mps
post_event_speed_mps
post_event_yaw_rate_abs
post_event_offtrack_overshoot
recoverability_window_success
```

Usage rules:

```text
do not impute these fields;
do not use impact_speed_proxy as delta-v;
do not claim post-event recovery;
do not claim post-collision controllability;
do not mark R4 mitigation fully measured until these are supported or explicitly
scoped out.
```

## Proposed Artifact-Only Semantics Labels

M2333 should produce one row per R4 scenario with these semantic labels:

```text
r4_role_semantics:
  unavoidable_mitigation

obstacle_passage_success_semantics:
  insufficient_for_r4

impact_proxy_semantics:
  available
  unavailable

post_collision_semantics:
  blocked_current_sim_collision_terminates
  available

r4_metric_semantics_status:
  proxy_metric_available_post_collision_blocked
  proxy_metric_unavailable
  post_collision_metric_available

comparison_admissibility:
  descriptive_proxy_audit_only
  blocked_until_semantics_audited
```

For M2330, the expected dominant status is:

```text
proxy_metric_available_post_collision_blocked
```

This means the current simulator can support a descriptive impact-proxy audit,
but not a final mitigation-performance comparison.

## Proposed Artifact Outputs

M2333 should implement an artifact-only script that writes:

```text
runs/m2333_paper_route_current_sim_r4_mitigation_metric_semantics/r4_metric_semantics_rows.csv
runs/m2333_paper_route_current_sim_r4_mitigation_metric_semantics/r4_metric_proxy_policy_aggregate.csv
runs/m2333_paper_route_current_sim_r4_mitigation_metric_semantics/r4_claim_boundary.csv
runs/m2333_paper_route_current_sim_r4_mitigation_metric_semantics/summary.json
```

`r4_metric_semantics_rows.csv` should include:

```text
scenario_spec_id
role_family
episode_count
collision_count
offtrack_count
impact_proxy_available_count
impact_proxy_available_fraction
post_collision_available_count
obstacle_passage_success_semantics
impact_proxy_semantics
post_collision_semantics
r4_metric_semantics_status
comparison_admissibility
ranking_admissible
winner_selected
paper_level_claim_made
level3_self_id_claim_made
```

`r4_metric_proxy_policy_aggregate.csv` may include per-support-policy
descriptive aggregates, but every row must keep:

```text
ranking_admissible: false
winner_selected: false
```

It must not sort, select, promote, or recommend a support policy.

`summary.json` should report at least:

```text
scenario_count
episode_count
impact_proxy_available_scenario_count
post_collision_blocked_scenario_count
obstacle_passage_success_insufficient_count
ranking_admissible_count
winner_selected_count
guardrail_violation_count
result_class
next_blocker
```

## Guardrails

M2333 must not:

```text
run environment reset or rollout;
execute policy actions;
train replay PPO or promote;
rank support policies or controller families;
select a winner;
make paper-level or level3 self-ID claims;
add mitigation metrics to actor input;
change reward or collision termination;
fabricate delta-v or post-collision recovery fields.
```

## Decision

M2332 admits an artifact-only implementation:

```text
next: m2333-paper-route-current-sim-r4-mitigation-metric-semantics-implementation
```

Allowed claim:

```text
M2332 defines bounded current-sim R4 mitigation metric semantics and admits an
artifact-only implementation route.
```

Blocked claims:

```text
R4 mitigation solved;
support policies ranked;
controller families ranked;
winner selected;
paper-level evidence;
finite-window vs GRU conclusion;
level3 self-identification evidence;
post-collision mitigation measured.
```

## Follow-Up Manifest

```text
experiments/manifests/m2333-paper-route-current-sim-r4-mitigation-metric-semantics-implementation.json
```
