# M1781 Paper-Route Role-Specific Metric Scorecard Design

- status: completed
- decision: `role_specific_scorecard_design_admit_no_rollout_extraction`
- parent synthesis: `docs/m1780-paper-route-metric-specific-bounded-panel-branch-synthesis.md`
- no reset: true
- no rollout: true
- training/replay/PPO: false

## Summary

M1781 defines a role-specific metric scorecard over the existing M1777 bounded
panel artifacts. The design deliberately avoids global success ranking. Each
role gets primary metrics, guardrail metrics, and ranking blockers that match
the role's intended claim.

This design admits M1782 no-rollout scorecard extraction. M1782 should compute
tables from M1777 `episode_rows.csv` only; it must not rerun the environment or
rank profiles.

## Inputs

Fixed source artifacts:

```text
runs/m1777_metric_specific_bounded_panel_measured_execution/episode_rows.csv
runs/m1777_metric_specific_bounded_panel_measured_execution/summary.json
runs/m1779_metric_specific_bounded_panel_outcome_localization/summary.json
```

The scorecard must preserve:

- `profile_name`;
- `role_panel_id`;
- `primary_metric_family`;
- hidden-dynamics, road, timing, lateral, and sampled-label buckets;
- diagnostic-only no-ranking flags.

## Role Score Contracts

### stable_avoidance_aes

Primary metrics:

- `success_obstacle_pass_rate`;
- `collision_failure_rate`;
- `off_track_noncollision_noncompletion_rate`;
- `recovery_success_rate`;
- `clearance_margin_p10`.

Admissibility blockers:

- collision rate is nonzero beyond a small tolerance;
- off-track noncompletion dominates the role;
- metric completeness fails;
- role sample count is below the fixed `72` cells.

Allowed claim after extraction:

- stable avoidance/AES diagnostic quality only, pending audit.

### drift_required_recovery

Primary metrics:

- `controlled_drift_recovery_success_rate`;
- `drift_used_rate`;
- `recovery_success_rate`;
- `collision_failure_rate`;
- `off_track_noncollision_noncompletion_rate`;
- `recovery_time_proxy_mean`.

Admissibility blockers:

- drift is not used on drift-required rows;
- recovery success is near zero;
- collision or off-track dominates;
- metric completeness fails.

Allowed claim after extraction:

- drift-recovery diagnostic quality only, pending audit.

### hidden_dynamics_robustness

Primary metrics:

- worst hidden-dynamics bucket success rate;
- worst hidden-dynamics bucket collision rate;
- worst hidden-dynamics bucket off-track rate;
- success-rate spread across hidden buckets;
- recovery and controlled-drift degradation across hidden buckets.

Admissibility blockers:

- one hidden bucket collapses;
- profile behavior is driven by one public bucket;
- current-frame or profile effects cannot be separated from hidden-dynamics
  effects;
- metric completeness fails.

Allowed claim after extraction:

- hidden-dynamics robustness diagnostic quality only, pending audit.

### unavoidable_mitigation

Primary metrics:

- `impact_severity_proxy_mean`;
- `collision_mitigation_score_mean`;
- `impact_speed_proxy_mean`;
- `impact_beta_abs_mean`;
- `impact_yaw_rate_abs_mean`;
- `off_track_severity_proxy_mean`.

Admissibility blockers:

- obstacle-pass success is used as the primary metric;
- collision existence is treated as failure rather than mitigation context;
- impact metrics are missing for collision rows;
- off-track replaces collision mitigation behavior.

Allowed claim after extraction:

- unavoidable-collision mitigation severity only, pending audit.

## Output Tables For M1782

M1782 should write:

```text
summary.json
profile_role_scorecard.csv
role_panel_scorecard.csv
profile_role_hidden_bucket_scorecard.csv
profile_role_sampled_label_scorecard.csv
role_admissibility.csv
ranking_blockers.csv
metric_contract.csv
```

The scorecard rows should include `ranking_admissible_after_audit=false` by
default. A later audit may decide whether any limited role-specific comparison
is admissible.

## Score Direction

M1782 may compute normalized helper columns, but it must not collapse them into
a single leaderboard. If directional fields are added:

- higher is better for obstacle pass, recovery, controlled drift recovery, and
  clearance margin;
- lower is better for collision rate, off-track rate, impact severity, impact
  speed, impact beta, impact yaw rate, and recovery time;
- unavoidable mitigation must not use obstacle-pass success as a primary
  positive score.

## Guardrails

- environment reset started: `false`
- environment rollout started: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- reward changed: `false`
- dynamics changed: `false`
- termination behavior changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Claim Boundary

Supported:

- role-specific scorecard design;
- no-rollout scorecard extraction is admitted;
- global ranking remains blocked.

Unsupported:

- profile ranking;
- profile promotion;
- private-holdout evidence;
- paper-level benchmark evidence;
- level3 self-identification.

## Decision

Route to M1782 no-rollout role-specific scorecard extraction implementation.
