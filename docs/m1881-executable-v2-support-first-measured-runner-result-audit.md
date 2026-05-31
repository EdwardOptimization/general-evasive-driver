# M1881 Executable V2 Support-First Measured Runner Result Audit

- status: completed
- decision: `support_first_result_audit_route_to_outcome_localization`
- synthesis decision: `continue`
- branch: `paper_route_executable_v2_support_first_measured_execution`
- audited summary: `runs/m1880_executable_v2_support_first_measured_runner_execution/summary.json`
- audited episode rows: `runs/m1880_executable_v2_support_first_measured_runner_execution/episode_rows.csv`
- reset/rollout in M1881: false
- training/replay/PPO: false

## Evidence Summary

M1880 satisfies the execution pass criteria:

```text
result_class: executable_v2_support_first_measured_runner_execution_pass
episode_count: 2160 / 2160
failure_count: 0
controller_profile_count: 12 / 12
support_first_spec_count: 180 / 180
role_panel_count: 4 / 4
role_surface_count: 8 / 8
profile_alias_mismatch_count: 0
all_selected_metrics_finite: true
metric_completeness_passed: true
metric_completeness_failure_count: 0
guardrail_violation_count: 0
```

The measured outcome distribution is dominated by non-success:

```text
success_obstacle_pass: 0
collision_failure: 480
off_track_noncollision_noncompletion: 1680
```

Role panel outcome rates:

```text
drift_required_recovery:
  collision_failure_rate: 0.232639
  off_track_noncollision_noncompletion_rate: 0.767361

stable_aeb:
  collision_failure_rate: 0.112847
  off_track_noncollision_noncompletion_rate: 0.887153

stable_aes_only:
  collision_failure_rate: 0.001736
  off_track_noncollision_noncompletion_rate: 0.998264

unavoidable_mitigation:
  collision_failure_rate: 0.648148
  off_track_noncollision_noncompletion_rate: 0.351852
```

This means M1880 is a valid public diagnostic execution artifact, but it is not
an interpretable controller-family comparison.

## Supported Claims

- The support-first measured runner can execute the fixed `2160`-cell workload
  completely.
- Support-first metadata, controller-profile identity, role panels, and
  role-surfaces are preserved in the measured artifacts.
- The measured artifacts are complete enough for no-rerun localization.
- No training, replay, PPO, profile tuning, promotion, private holdout,
  controller ranking, paper-level claim, or level3 self-ID claim occurred.

## Falsified Claims

- M1880 does not support controller-family ranking.
- M1880 does not support a paper-level benchmark claim.
- M1880 does not support a level3 self-identification claim.
- M1880 does not show that the current support-first task panel is already
  suitable for final profile comparison, because all profiles have zero
  `success_obstacle_pass` under the current metric.

## Failure Taxonomy Summary

Execution infrastructure failure: none.

Observed research blocker:

```text
outcome_dominance: success_obstacle_pass is zero across the full public diagnostic matrix
```

This is not a runner failure. It is a task-quality / metric-interpretation
blocker that must be localized before any repair or comparison.

## Public Gate Overfit Risk

Risk is high if the project responds by directly tuning controllers or task
parameters against this fixed 2160-row public matrix. The correct next step is
localization over existing artifacts:

- identify whether off-track termination occurs before obstacle pass;
- separate collision-heavy unavoidable cases from off-track-dominated stable
  cases;
- compare role-surface, hidden dynamics, road boundary, obstacle timing, and
  controller-profile slices;
- decide whether the blocker is scenario geometry, success semantics, road
  boundary strictness, controller weakness, or a mixture.

Private holdout remains unused.

## Next Branch Decision

Continue the support-first measured-execution branch into M1882 outcome
localization. M1882 should not rerun environment rollout. It should consume only
M1880 artifacts and produce localization tables that decide whether to route to:

```text
scenario/task-quality repair
success-metric semantics audit
controller-family task-quality repair
branch synthesis
later ranking design
```

Ranking remains blocked unless a later audit explicitly admits it.

## Claim Boundary

Supported by M1881:

```text
M1880 execution pass verified
outcome dominance identified
ranking and paper claims blocked
M1882 no-rerun outcome localization admitted
```

Unsupported by M1881:

```text
controller-family ranking
policy improvement claim
paper-level benchmark result
level3 self-identification evidence
```

## Decision

Route to M1882 support-first outcome localization before any scenario repair,
training, profile ranking, or paper-route comparison.
