# M1778 Paper-Route Metric-Specific Bounded Panel Measured Execution Result Audit

- status: completed
- decision: `bounded_panel_result_audit_route_to_outcome_localization`
- audited summary: `runs/m1777_metric_specific_bounded_panel_measured_execution/summary.json`
- no reset in audit: true
- no rollout in audit: true
- training/replay/PPO: false

## Summary

M1778 audits the M1777 bounded-panel measured execution before any ranking,
paper-level claim, or scenario repair. The execution itself passes. The outcome
distribution, however, is not directly interpretable as a controller-family
ranking because non-success outcomes are role- and profile-sensitive.

Observed M1777 state:

```text
result_class: metric_specific_bounded_panel_measured_execution_pass
episode_count: 288 / 288
failure_count: 0
profile_count: 12 / 12
bounded_panel_spec_count: 24 / 24
role_panel_count: 4 / 4
all_selected_metrics_finite: true
metric_completeness_passed: true
metric_completeness_failure_count: 0
guardrail_violation_count: 0
```

## Outcome Audit

Overall outcome counts:

```text
success_obstacle_pass: 24
collision_failure: 122
off_track_noncollision_noncompletion: 142
```

Role-level outcome rates:

```text
stable_avoidance_aes:
  success_obstacle_pass_rate: 0.069444
  collision_failure_rate: 0.013889
  off_track_noncollision_noncompletion_rate: 0.916667

drift_required_recovery:
  success_obstacle_pass_rate: 0.152778
  collision_failure_rate: 0.305556
  off_track_noncollision_noncompletion_rate: 0.541667

hidden_dynamics_robustness:
  success_obstacle_pass_rate: 0.069444
  collision_failure_rate: 0.430556
  off_track_noncollision_noncompletion_rate: 0.500000

unavoidable_mitigation:
  success_obstacle_pass_rate: 0.041667
  collision_failure_rate: 0.944444
  off_track_noncollision_noncompletion_rate: 0.013889
```

This is coherent with the role structure in some places, especially
`unavoidable_mitigation`, but it also shows strong off-track dominance in
`stable_avoidance_aes` and mixed collision/off-track behavior in
`hidden_dynamics_robustness`. Directly ranking profiles from the global success
rate would therefore conflate role semantics with failure mode distribution.

## Audit Findings

M1777 satisfies its execution gates:

- exact `288` episode count;
- zero failure rows;
- exact `12` profiles;
- exact `24` bounded-panel specs;
- exact `4` role panels;
- finite selected metrics;
- metric completeness passed;
- required aggregates are written;
- no training, replay, PPO, promotion, private holdout, actor-input change,
  profile-specific tuning, controller-family ranking claim, paper-level claim,
  or level3 self-ID claim occurred.

M1777 does not yet satisfy an interpretation gate for controller-family
ranking. The result needs a no-rollout localization pass over existing
`episode_rows.csv` and aggregates to identify whether the dominant outcomes are
role-expected, profile-specific, metric-specific, or panel-design artifacts.

## Route Decision

Route to M1779 bounded-panel outcome localization.

M1779 should:

- use only M1777 artifacts;
- not rerun reset or rollout;
- localize outcome dominance by role panel, profile, primary metric family,
  hidden dynamics bucket, road bucket, obstacle timing, obstacle lateral bucket,
  and sampled label;
- identify target slices that block ranking;
- decide whether to admit role-specific ranking design, scenario/metric repair,
  or branch synthesis.

## Guardrails

- environment reset started in audit: `false`
- environment rollout started in audit: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Claim Boundary

Supported:

- M1777 is a complete bounded-panel measured public diagnostic execution;
- ranking remains blocked pending outcome localization.

Unsupported:

- controller-family ranking;
- profile promotion;
- private-holdout evidence;
- paper-level benchmark evidence;
- level3 self-identification;
- any claim that global success rate represents driver quality.

## Decision

Route to M1779 no-rollout bounded-panel outcome localization.
