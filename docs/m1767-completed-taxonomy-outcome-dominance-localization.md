# M1767 Completed Taxonomy Outcome-Dominance Localization

- status: completed
- result class: `task_quality_outcome_dominance_localization_pass`
- summary: `runs/m1767_completed_taxonomy_outcome_dominance_localization/summary.json`
- parent audit: `docs/m1766-completed-taxonomy-outcome-audit.md`
- no rollout: true
- training/replay/PPO: false

## Summary

M1767 localizes the completed M1764 taxonomy outcome dominance from existing
episode rows only. It does not run environment rollout, train, replay, run PPO,
promote a checkpoint, use private holdout data, change actor inputs, tune
profiles, rank controller families, or make paper-level/level3 claims.

The localization passes as a diagnostic artifact, but it confirms the outcome
problem is still diffuse:

```text
episode_count: 864
dominant_slice_count: 305
target_dominant_slice_count: 291
dominant_family_count: 6
dominant_profile_count: 12
outcome_dominance_class: diffuse_outcome_dominance
guardrail_violation_count: 0
```

All target localization slice types are represented, including evaluation role,
primary metric family, scenario family, profile, hidden dynamics, road boundary,
obstacle timing, and obstacle lateral buckets.

## Role And Metric Localization

Evaluation role outcomes:

```text
benchmark:
  success 0.0949, collision 0.1157, off_track 0.7894
diagnostic_stress:
  success 0.0972, collision 0.3194, off_track 0.5833
mitigation_diagnostic:
  success 0.0278, collision 0.9583, off_track 0.0139
```

Primary metric family outcomes:

```text
avoidance_success:
  success 0.0556, collision 0.0486, off_track 0.8958
boundary_robustness:
  success 0.0694, collision 0.1875, off_track 0.7431
collision_mitigation:
  success 0.0278, collision 0.9583, off_track 0.0139
controlled_drift_recovery:
  success 0.1736, collision 0.2500, off_track 0.5764
hidden_dynamics_robustness:
  success 0.1250, collision 0.4514, off_track 0.4236
```

Interpretation: ordinary avoidance and boundary/stable-AES rows are mainly
off-track dominated, while mitigation rows are collision dominated. This is not
a single-profile or single-family defect.

## Scenario And Context Localization

Scenario family outcomes:

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

Context buckets:

```text
hidden_dynamics:
  actuator_delay collision 0.7083
  friction_step off_track 0.8073
  mild_randomization off_track 0.9583
road_boundary:
  nominal off_track 0.9167
  wide collision 0.4683
timing:
  very_close collision 0.7153
  medium_late off_track 0.9583
lateral:
  wide_offset off_track 0.7000
  center collision 0.4841
```

The top dominant slices are diagnostic-only. The strongest rows include
mitigation-diagnostic profile slices with `1.0` collision rate and ordinary or
stable-AES profile slices with `1.0` off-track rate.

## Artifacts

Key outputs:

- `runs/m1767_completed_taxonomy_outcome_dominance_localization/summary.json`
- `runs/m1767_completed_taxonomy_outcome_dominance_localization/dominant_slices.csv`
- `runs/m1767_completed_taxonomy_outcome_dominance_localization/target_dominant_slices.csv`
- `runs/m1767_completed_taxonomy_outcome_dominance_localization/evaluation_role_aggregate.csv`
- `runs/m1767_completed_taxonomy_outcome_dominance_localization/primary_metric_family_aggregate.csv`
- `runs/m1767_completed_taxonomy_outcome_dominance_localization/scenario_family_lateral_bucket_aggregate.csv`
- `runs/m1767_completed_taxonomy_outcome_dominance_localization/profile_evaluation_role_aggregate.csv`
- `runs/m1767_completed_taxonomy_outcome_dominance_localization/profile_primary_metric_aggregate.csv`

The localization tool was also extended to write the required M1767 target
slice aggregates while preserving the older M1740-style outputs.

## Guardrails

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

- completed taxonomy outcome dominance is localized into durable artifacts;
- dominance is diffuse across all `6` scenario families and all `12` profiles;
- ranking and paper-level interpretation remain blocked.

Unsupported:

- controller-family ranking;
- best-profile selection;
- private-holdout evidence;
- paper-level benchmark evidence;
- level3 self-identification.

## Decision

Route to M1768 completed taxonomy outcome-dominance result audit.

M1768 should decide whether the next branch is task-quality repair design,
metric-semantics audit, branch synthesis, or a bounded diagnostic panel. It must
not rank controller families from M1764/M1767 because the diffuse dominance
still confounds profile comparison.
