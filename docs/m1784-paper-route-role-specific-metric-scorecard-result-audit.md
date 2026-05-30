# M1784 Paper-Route Role-Specific Metric Scorecard Result Audit

- status: completed
- decision: `scorecard_result_audit_blocks_ranking_route_to_blocker_localization`
- audited summary: `runs/m1783_role_specific_metric_scorecard_extraction/summary.json`
- no reset in audit: true
- no rollout in audit: true
- training/replay/PPO: false

## Summary

M1784 audits the M1783 role-specific scorecard extraction before any ranking,
paper-level claim, or profile promotion. The extraction itself passes and the
metric contract is coherent. The audit keeps ranking blocked because every role
panel remains diagnostic-only and the blockers are role-specific.

Observed M1783 state:

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

## Contract Audit

The required scorecard artifacts exist:

```text
profile_role_scorecard.csv
role_panel_scorecard.csv
profile_role_hidden_bucket_scorecard.csv
profile_role_sampled_label_scorecard.csv
role_admissibility.csv
ranking_blockers.csv
metric_contract.csv
summary.json
```

The mitigation contract is preserved: `unavoidable_mitigation` uses
`impact_severity_proxy_mean` as its primary metric with `lower` as the preferred
direction. It does not use `success_obstacle_pass_rate` as the primary metric.

All scorecard rows keep `diagnostic_only_no_ranking_claim=true` and
`ranking_admissible_after_audit=false`.

## Blocker Audit

Role-level blockers:

```text
stable_avoidance_aes:
  stable_off_track_dominance
  stable_success_low

drift_required_recovery:
  drift_controlled_recovery_low
  drift_non_success_dominance

hidden_dynamics_robustness:
  hidden_success_low
  hidden_non_success_dominance

unavoidable_mitigation:
  ranking_blocked_pending_audit
```

Role panel metrics explain why a direct controller-family ranking is not yet
valid:

```text
stable_avoidance_aes:
  success_obstacle_pass_rate: 0.069444
  collision_failure_rate: 0.013889
  off_track_noncollision_noncompletion_rate: 0.916667

drift_required_recovery:
  controlled_drift_recovery_success_rate: 0.027778
  drift_used_rate: 0.333333
  collision_failure_rate: 0.305556
  off_track_noncollision_noncompletion_rate: 0.541667

hidden_dynamics_robustness:
  success_obstacle_pass_rate: 0.069444
  collision_failure_rate: 0.430556
  off_track_noncollision_noncompletion_rate: 0.500000

unavoidable_mitigation:
  impact_severity_proxy_mean: 17.470257
  collision_failure_rate: 0.944444
  off_track_noncollision_noncompletion_rate: 0.013889
```

The profile-level scorecard contains useful diagnostic signals, for example
`L3_online_gru` and `L3_reset_control_corrected` are among the best rows for
some role metrics. Those cells have only six episodes each, however, and the
role-level blockers are still active. They are not ranking evidence.

## Audit Findings

M1783 satisfies its extraction gates:

- exact `288` episode count;
- exact `12` profiles;
- exact `4` role panels;
- complete profile-role, role-panel, hidden-bucket, sampled-label,
  admissibility, blocker, and metric-contract artifacts;
- mitigation does not use obstacle-pass success as a primary metric;
- guardrail violation count is zero;
- no reset, rollout, training, replay, PPO, promotion, private holdout,
  actor-input change, profile-specific tuning, controller-family ranking claim,
  paper-level claim, or level3 self-ID claim occurred.

M1783 does not admit ranking. The blockers are coherent enough to justify a
next no-rollout localization step:

- stable avoidance is dominated by off-track noncompletion rather than
  collision;
- drift-required recovery has very low controlled recovery;
- hidden-dynamics robustness is split between collision and off-track failures;
- unavoidable mitigation needs impact-severity localization rather than
  obstacle-pass success interpretation.

## Route Decision

Route to M1785 role-specific scorecard blocker localization.

M1785 should:

- use only M1783 scorecard artifacts;
- not rerun reset or rollout;
- localize blockers by role, profile, hidden dynamics bucket, sampled label,
  and primary metric;
- preserve diagnostic-only scorecard semantics;
- decide whether the following branch should be scenario/metric repair,
  branch synthesis, or a tightly scoped role-specific comparison design.

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

- M1783 is a complete no-rollout role-specific scorecard extraction;
- the role-specific metric contract is coherent;
- ranking remains blocked;
- blocker localization is the next necessary process step.

Unsupported:

- controller-family ranking;
- profile promotion;
- private-holdout evidence;
- paper-level benchmark evidence;
- level3 self-identification;
- any claim that role-specific scorecards already support a paper comparison.
