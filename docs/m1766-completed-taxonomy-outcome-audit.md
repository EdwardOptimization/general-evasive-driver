# M1766 Completed Taxonomy Outcome Audit

- status: completed
- decision: `completed_outcome_audit_blocks_ranking_admit_outcome_dominance_localization`
- audited output: `runs/m1764_revised_scenario_taxonomy_single_seed_completion`
- no rollout: true
- training/replay/PPO: false

## Summary

M1766 audits the completed M1764 taxonomy outcomes using existing aggregate
artifacts only. The completed artifact is valid, but outcome dominance still
blocks controller-family ranking and paper-level interpretation.

Overall outcomes:

```text
success_obstacle_pass: 73 / 864 = 0.0845
collision_failure: 280 / 864 = 0.3241
off_track_noncollision_noncompletion: 511 / 864 = 0.5914
```

The matrix is complete, but it is not yet a clean benchmark result. The next
step should localize outcome dominance across family, role, metric family, and
profile slices before any repair or comparison decision.

## By Evaluation Role

```text
benchmark:
  success: 41 / 432 = 0.0949
  collision: 50 / 432 = 0.1157
  off_track: 341 / 432 = 0.7894

diagnostic_stress:
  success: 28 / 288 = 0.0972
  collision: 92 / 288 = 0.3194
  off_track: 168 / 288 = 0.5833

mitigation_diagnostic:
  success: 4 / 144 = 0.0278
  collision: 138 / 144 = 0.9583
  off_track: 2 / 144 = 0.0139
```

Interpretation:

- benchmark rows are dominated by off-track noncompletion;
- diagnostic-stress rows are split between off-track and collision failure;
- mitigation-diagnostic rows are dominated by collision, which may be expected
  for unavoidable scenarios but still requires metric-family-specific audit.

## By Scenario Family

```text
ordinary_stable_avoidance:
  success 0.0278, collision 0.0417, off_track 0.9306
aeb_infeasible_stable_aes:
  success 0.0833, collision 0.0556, off_track 0.8611
off_track_boundary_stress:
  success 0.0694, collision 0.1875, off_track 0.7431
drift_required_avoidance:
  success 0.1736, collision 0.2500, off_track 0.5764
hidden_dynamics_stress:
  success 0.1250, collision 0.4514, off_track 0.4236
unavoidable_mitigation:
  success 0.0278, collision 0.9583, off_track 0.0139
```

The strongest problem is not a single family. Ordinary avoidance and stable AES
are overwhelmingly off-track dominated, while unavoidable mitigation is
collision dominated by design/metric role. This needs localization before
deciding whether to repair task quality, profile behavior, or evaluation
semantics.

## By Profile

Profile success rates:

```text
L3_online_gru: 0.3194
L3_reset_control_corrected: 0.2500
L1_one_step: 0.2083
L0_current_masked: 0.1528
L2_window_13_current_tiled: 0.0139
L2_window_25: 0.0139
L2_window_50: 0.0139
L2_window_50_current_tiled: 0.0139
L2_window_100_current_tiled: 0.0139
L2_window_13: 0.0139
L2_window_25_current_tiled: 0.0000
L2_window_100: 0.0000
```

This suggests useful profile differences exist, especially for `L3_online_gru`,
but ranking is still blocked because broad task-quality failures dominate the
matrix.

## Ranking Decision

Controller-family ranking is not admissible yet.

Reasons:

- overall success is only `0.0845`;
- benchmark rows are `0.7894` off-track;
- several scenario families are dominated by off-track noncompletion;
- mitigation rows need metric-family-specific interpretation because collision
  may be an expected outcome class, but raw success remains low;
- profile differences may be real but are confounded by broad scenario outcome
  dominance.

## Guardrails

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
- profile configs changed: `false`
- scenario specs changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Claim Boundary

Supported:

- completed taxonomy outcome audit;
- ranking is blocked by outcome dominance;
- localization is needed before task repair or controller-family comparison.

Unsupported:

- controller-family ranking;
- paper-level benchmark evidence;
- private-holdout evidence;
- level3 self-identification evidence.

## Decision

Route to M1767 completed taxonomy outcome-dominance localization over existing
M1764 rows. M1767 should identify dominant target slices by evaluation role,
metric family, scenario family, profile, hidden dynamics, and road/timing
buckets without running new rollouts.
