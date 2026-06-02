# M2331 Paper-Route Current-Sim R4 Metric-Instrumented Support Diagnostic Rerun Result Audit

- status: completed
- result_class: `r4_metric_instrumented_support_diagnostic_result_accepted_route_to_r4_mitigation_semantics_design`
- manifest: `experiments/manifests/m2331-paper-route-current-sim-r4-metric-instrumented-support-diagnostic-rerun-result-audit.json`
- parent run: `runs/m2330_paper_route_current_sim_r4_metric_instrumented_support_diagnostic_rerun/summary.json`
- reset/rollout/policy action in M2331: `false`
- measured execution in M2331: `false`
- training/replay/PPO: `false`
- support-policy ranking claim made: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Audit Inputs

```text
runs/m2330_paper_route_current_sim_r4_metric_instrumented_support_diagnostic_rerun/summary.json
runs/m2330_paper_route_current_sim_r4_metric_instrumented_support_diagnostic_rerun/episode_rows.csv
runs/m2330_paper_route_current_sim_r4_metric_instrumented_support_diagnostic_rerun/r4_metric_field_completeness.csv
runs/m2330_paper_route_current_sim_r4_metric_instrumented_support_diagnostic_rerun/scenario_support_labels.csv
runs/m2330_paper_route_current_sim_r4_metric_instrumented_support_diagnostic_rerun/role_support_summary.csv
```

M2331 does not run new environment resets, rollouts, measured execution,
training, replay, PPO, ranking, or promotion.

## M2330 Completeness Decision

M2330 is accepted as a complete R4 metric-instrumented support diagnostic
artifact:

```text
result_class: current_sim_r4_metric_instrumented_support_diagnostic_rerun_pass
scenario_spec_count: 12 / 12
support_policy_count: 3 / 3
seed_repeat_count: 5
episode_count: 180 / 180
failure_count: 0
validation_failure_count: 0
metadata_missing_count: 0
metric_completeness_failure_count: 0
non_r4_role_count: 0
guardrail_violation_count: 0
required_r4_export_missing_field_count: 0
```

The diagnostic subset is source-correct:

```text
role_family_counts:
  R4_unavoidable_mitigation: 180

support_policy_counts:
  aeb: 60
  aes: 60
  envelope_aes: 60
```

## Field Availability Audit

The required R4 export fields are present. Impact and collision-time proxy
fields are available for the 173 collision rows:

```text
impact_speed_mps: finite 173 / 180
time_to_collision_s: finite 173 / 180
collision_side_proxy: nonempty 173 / 180
impact_speed_proxy: finite 173 / 180
impact_beta_abs: finite 173 / 180
impact_yaw_rate_abs: finite 173 / 180
impact_severity_proxy: finite 173 / 180
collision_mitigation_score: finite 180 / 180
```

The remaining canonical post-collision fields are correctly unavailable rather
than fabricated:

```text
delta_v_at_impact_mps_available: true 0 / 180
post_event_speed_mps_available: true 0 / 180
recoverability_window_success_available: true 0 / 180
```

This means current collision-terminating rollouts can support a bounded
impact-proxy mitigation semantics audit, but they cannot yet support true
delta-v, post-event recovery, or post-collision controllability claims.

## Outcome Audit

Global R4 diagnostic outcomes:

```text
global_success_count: 0
global_collision_count: 173
global_offtrack_count: 6
global_obstacle_completed_count: 0

global_success_rate: 0.0
global_collision_rate: 0.9611111111111111
global_offtrack_rate: 0.03333333333333333
```

Outcome buckets:

```text
collision_failure: 173
off_track_noncollision_noncompletion: 6
max_steps_noncompletion: 1
```

Role support summary:

```text
R4_unavoidable_mitigation:
  scenario_count: 12
  support_clear_count: 0
  support_mixed_count: 3
  support_blocked_count: 9
  metric_conflict_count: 0
```

The key audit point is that R4 is an unavoidable-mitigation role. Pure obstacle
passage success is not the right final semantic target for this role. M2330
shows the support policies mostly collide, but now exposes impact-speed,
impact-severity, collision-time, and collision-side proxy fields needed to
define a bounded mitigation metric semantics layer.

## Non-Ranking Policy Snapshot

The following support-policy aggregates are diagnostic only:

```text
aeb:
  rows: 60
  success: 0
  collision: 59
  offtrack: 1
  impact_speed_mps mean over collisions: 15.066808872218932
  collision_mitigation_score mean: 15.776193809417634

aes:
  rows: 60
  success: 0
  collision: 58
  offtrack: 1
  impact_speed_mps mean over collisions: 13.623987417835046
  collision_mitigation_score mean: 14.163401872742776

envelope_aes:
  rows: 60
  success: 0
  collision: 56
  offtrack: 4
  impact_speed_mps mean over collisions: 16.161697154698228
  collision_mitigation_score mean: 15.80956853098948
```

M2331 does not interpret these as a policy ranking or winner selection. They
only show that mitigation-proxy fields are populated enough to design a
role-specific semantics audit.

## Decision

M2331 accepts M2330 and routes to an artifact-only R4 mitigation metric
semantics design:

```text
next: m2332-paper-route-current-sim-r4-mitigation-metric-semantics-design
```

The next design should define:

```text
1. Which R4 proxy fields can be used for current-sim mitigation semantics.
2. Which unavailable canonical fields remain blocked.
3. How to avoid ranking support policies while auditing metric semantics.
4. Whether R4 residual support rows should be relabeled as metric-available,
   metric-blocked, or post-collision-continuation-required.
5. What artifact-only implementation should produce before any controller
   comparison resumes.
```

## Claim Boundary

Allowed claim:

```text
M2331 accepts M2330 as a complete diagnostic artifact and selects bounded R4
mitigation metric semantics design as the next non-ranking route.
```

Blocked claims:

```text
support policies ranked;
controller families ranked;
winner selected;
R4 mitigation solved;
mitigation performance proven;
paper-level evidence;
finite-window vs GRU conclusion;
level3 self-identification evidence.
```

## Follow-Up Manifest

```text
experiments/manifests/m2332-paper-route-current-sim-r4-mitigation-metric-semantics-design.json
```
