# M1783 Role-Specific Metric Scorecard Extraction

- status: completed
- decision: `role_specific_scorecard_extraction_pass_route_to_result_audit`
- summary: `runs/m1783_role_specific_metric_scorecard_extraction/summary.json`
- no reset: true
- no rollout: true
- training/replay/PPO: false

## Summary

M1783 ran the no-rollout role-specific scorecard extractor from M1782 over the
fixed M1777 bounded-panel episode rows. It did not rerun reset, rollout, replay,
PPO, or training.

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.role_specific_metric_scorecard \
  --episode-rows runs/m1777_metric_specific_bounded_panel_measured_execution/episode_rows.csv \
  --output-dir runs/m1783_role_specific_metric_scorecard_extraction \
  --target-episode-count 288 \
  --next-blocker m1784-paper-route-role-specific-metric-scorecard-result-audit
```

Result:

```text
result_class: role_specific_metric_scorecard_extraction_pass
episode_count: 288 / 288
profile_count: 12 / 12
role_panel_count: 4 / 4
profile_role_scorecard_rows: 48
role_panel_scorecard_rows: 4
profile_role_hidden_bucket_scorecard_rows: 144
profile_role_sampled_label_scorecard_rows: 78
role_admissibility_rows: 4
ranking_blocker_rows: 7
metric_contract_rows: 20
mitigation_contract_uses_success_as_primary: false
ranking_admissible_after_audit: false
guardrail_violation_count: 0
```

Written artifacts:

```text
runs/m1783_role_specific_metric_scorecard_extraction/summary.json
runs/m1783_role_specific_metric_scorecard_extraction/profile_role_scorecard.csv
runs/m1783_role_specific_metric_scorecard_extraction/role_panel_scorecard.csv
runs/m1783_role_specific_metric_scorecard_extraction/profile_role_hidden_bucket_scorecard.csv
runs/m1783_role_specific_metric_scorecard_extraction/profile_role_sampled_label_scorecard.csv
runs/m1783_role_specific_metric_scorecard_extraction/role_admissibility.csv
runs/m1783_role_specific_metric_scorecard_extraction/ranking_blockers.csv
runs/m1783_role_specific_metric_scorecard_extraction/metric_contract.csv
```

## Role Admissibility Snapshot

The extraction preserved the M1781 contract: scorecards are diagnostic only and
do not admit controller-family ranking.

```text
stable_avoidance_aes:
  ranking_admissible_after_audit: false
  blockers: stable_off_track_dominance; stable_success_low

drift_required_recovery:
  ranking_admissible_after_audit: false
  blockers: drift_controlled_recovery_low; drift_non_success_dominance

hidden_dynamics_robustness:
  ranking_admissible_after_audit: false
  blockers: hidden_success_low; hidden_non_success_dominance

unavoidable_mitigation:
  ranking_admissible_after_audit: false
  blockers: ranking_blocked_pending_audit
```

Role panel primary metrics:

```text
stable_avoidance_aes:
  primary_role_metric: success_obstacle_pass_rate
  primary_role_metric_value: 0.069444
  collision_failure_rate: 0.013889
  off_track_noncollision_noncompletion_rate: 0.916667

drift_required_recovery:
  primary_role_metric: controlled_drift_recovery_success_rate
  primary_role_metric_value: 0.027778
  drift_used_rate: 0.333333
  collision_failure_rate: 0.305556
  off_track_noncollision_noncompletion_rate: 0.541667

hidden_dynamics_robustness:
  primary_role_metric: success_obstacle_pass_rate
  primary_role_metric_value: 0.069444
  collision_failure_rate: 0.430556
  off_track_noncollision_noncompletion_rate: 0.500000

unavoidable_mitigation:
  primary_role_metric: impact_severity_proxy_mean
  primary_role_metric_value: 17.470257
  primary_role_metric_direction: lower
  collision_failure_rate: 0.944444
```

The unavoidable mitigation role does not use obstacle-pass success as its
primary metric.

## Guardrails

- environment reset started: `false`
- environment rollout started: `false`
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

- no-rollout role-specific scorecard extraction over M1777 succeeded;
- all required scorecard artifacts were written;
- the mitigation metric contract preserved the M1781 design;
- ranking remains blocked pending M1784 audit.

Unsupported:

- controller-family ranking;
- profile promotion;
- private-holdout evidence;
- paper-level benchmark evidence;
- level3 self-identification;
- any claim that the scorecards are ready for paper-level comparison.

## Decision

Route to M1784 role-specific metric scorecard result audit. M1784 should use
only the M1783 artifacts, audit the blockers and metric contract, and decide
whether the next branch is role-slice localization, metric/scenario repair,
branch synthesis, or a tightly scoped comparison design.
