# M1785 Role-Specific Scorecard Blocker Localization

- status: completed
- decision: `scorecard_blocker_localization_route_to_role_specific_panel_repair_design`
- source artifacts: `runs/m1783_role_specific_metric_scorecard_extraction/`
- no reset: true
- no rollout: true
- training/replay/PPO: false

## Summary

M1785 localizes the M1783/M1784 role-specific scorecard blockers using only
existing scorecard artifacts. The blockers are coherent and mostly role/panel
level, not a single-profile or single-hidden-bucket artifact. Ranking remains
blocked.

The next useful step is not controller-family ranking. It is a role-specific
panel/metric repair design that separates:

- stable AES road-boundary admissibility;
- drift-required controlled recovery;
- hidden-dynamics robustness by label and hidden bucket;
- unavoidable mitigation severity.

## Inputs

Used artifacts:

```text
runs/m1783_role_specific_metric_scorecard_extraction/profile_role_scorecard.csv
runs/m1783_role_specific_metric_scorecard_extraction/profile_role_hidden_bucket_scorecard.csv
runs/m1783_role_specific_metric_scorecard_extraction/profile_role_sampled_label_scorecard.csv
runs/m1783_role_specific_metric_scorecard_extraction/role_admissibility.csv
runs/m1783_role_specific_metric_scorecard_extraction/ranking_blockers.csv
runs/m1783_role_specific_metric_scorecard_extraction/metric_contract.csv
```

No environment reset, rollout, training, replay, PPO, private holdout, actor
input change, profile-specific tuning, or promotion was performed.

## Role Blockers

### stable_avoidance_aes

Blockers:

```text
stable_off_track_dominance
stable_success_low
```

Role aggregate:

```text
success_obstacle_pass_rate: 0.069444
collision_failure_rate: 0.013889
off_track_noncollision_noncompletion_rate: 0.916667
```

Hidden-bucket localization:

```text
brake_variation:
  success: 0.083
  collision: 0.000
  off_track: 0.917

friction_step:
  success: 0.083
  collision: 0.042
  off_track: 0.875

nominal:
  success: 0.056
  collision: 0.000
  off_track: 0.944
```

Sampled-label localization:

```text
aeb_feasible:
  success: 0.111
  collision: 0.028
  off_track: 0.861

aes_feasible:
  success: 0.028
  collision: 0.000
  off_track: 0.972
```

Conclusion: the stable AES blocker is pervasive off-track dominance across
hidden buckets and labels. It should be treated as a road-boundary/panel
admissibility blocker before any ranking.

### drift_required_recovery

Blockers:

```text
drift_controlled_recovery_low
drift_non_success_dominance
```

Role aggregate:

```text
controlled_drift_recovery_success_rate: 0.027778
drift_used_rate: 0.333333
success_obstacle_pass_rate: 0.152778
collision_failure_rate: 0.305556
off_track_noncollision_noncompletion_rate: 0.541667
```

Hidden-bucket localization:

```text
friction_step:
  success: 0.250
  collision: 0.375
  off_track: 0.375
  controlled_recovery: 0.042
  drift_used: 0.250

low_mu:
  success: 0.125
  collision: 0.292
  off_track: 0.583
  controlled_recovery: 0.000
  drift_used: 0.375

tire_stiffness:
  success: 0.083
  collision: 0.250
  off_track: 0.667
  controlled_recovery: 0.042
  drift_used: 0.375
```

Conclusion: drift-required recovery is not just lacking drift entry; drift is
used in roughly one third of episodes, but controlled recovery remains near
zero. The repair should separate drift initiation, obstacle clearance, and
post-maneuver recovery instead of ranking by a single success metric.

### hidden_dynamics_robustness

Blockers:

```text
hidden_success_low
hidden_non_success_dominance
```

Role aggregate:

```text
success_obstacle_pass_rate: 0.069444
collision_failure_rate: 0.430556
off_track_noncollision_noncompletion_rate: 0.500000
```

Hidden-bucket localization:

```text
actuator_delay:
  success: 0.125
  collision: 0.458
  off_track: 0.417

brake_drive_variation:
  success: 0.042
  collision: 0.458
  off_track: 0.500

mass_cg_shift:
  success: 0.042
  collision: 0.375
  off_track: 0.583
```

Sampled-label localization:

```text
aes_feasible:
  success: 0.111
  collision: 0.000
  off_track: 0.889

drift_required:
  success: 0.079
  collision: 0.316
  off_track: 0.605

unavoidable:
  success: 0.040
  collision: 0.760
  off_track: 0.200
```

Conclusion: hidden-dynamics robustness is label-mixed and failure-mode mixed.
The repair should split robustness by task label and hidden bucket before using
it as a comparison surface.

### unavoidable_mitigation

Blocker:

```text
ranking_blocked_pending_audit
```

Role aggregate:

```text
impact_severity_proxy_mean: 17.470257
collision_failure_rate: 0.944444
off_track_noncollision_noncompletion_rate: 0.013889
success_obstacle_pass_rate: 0.041667
```

Hidden-bucket localization:

```text
actuator_delay:
  collision: 1.000
  impact_severity: 18.171

brake_variation:
  collision: 1.000
  impact_severity: 18.553

low_mu:
  collision: 0.833
  impact_severity: 15.665
```

Conclusion: mitigation is semantically different from avoidance. The current
metric contract is reasonable because it uses impact severity, not obstacle-pass
success. It still needs a separate mitigation-specific comparison surface and
should not be combined with stable/drift/hidden avoidance ranking.

## Profile-Level Signals

Some profile rows are diagnostically useful but not rank-admissible. Examples:

```text
stable_avoidance_aes:
  best primary rows include L1_one_step and L3_online_gru at 0.333333 success,
  but both still have 0.666667 off-track rates.

drift_required_recovery:
  L3_online_gru and L3_reset_control_corrected reach 0.166667 controlled
  recovery, but each profile-role cell has only six episodes.

hidden_dynamics_robustness:
  L3_online_gru and L3_reset_control_corrected reach 0.333333 success, but
  role-level collision/off-track dominance remains active.

unavoidable_mitigation:
  the best impact severity rows are L2_window_13, L2_window_25, and
  L2_window_25_current_tiled, but mitigation severity cannot be mixed with
  obstacle-pass ranking.
```

These signals can inform later designs, but they are not sufficient for ranking
or paper-level comparison.

## Localization Decision

M1785 localizes the blockers as follows:

```text
stable_avoidance_aes:
  localized as pervasive off-track dominance across hidden buckets and labels

drift_required_recovery:
  localized as controlled-recovery deficit after drift/avoidance attempts

hidden_dynamics_robustness:
  localized as mixed task-label and mixed failure-mode dominance

unavoidable_mitigation:
  localized as a separate impact-severity task, not an avoidance-success task
```

Ranking remains blocked. The next route is role-specific panel/metric repair
design, not more scorecard extraction.

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

- M1783 scorecard blockers are localized from existing artifacts;
- ranking remains blocked;
- role-specific panel/metric repair is the next branch.

Unsupported:

- controller-family ranking;
- profile promotion;
- private-holdout evidence;
- paper-level benchmark evidence;
- level3 self-identification;
- any claim that current scorecards are ready for final comparison.
