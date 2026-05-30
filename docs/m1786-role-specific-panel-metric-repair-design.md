# M1786 Role-Specific Panel/Metric Repair Design

- status: completed
- decision: `role_specific_panel_metric_repair_design_admit_materialization_preflight`
- source: `docs/m1785-role-specific-scorecard-blocker-localization.md`
- no reset: true
- no rollout: true
- training/replay/PPO: false

## Summary

M1786 turns the M1785 blocker localization into a concrete repair design. The
main issue is not missing scorecard extraction. The issue is that the current
bounded panel mixes role semantics in ways that make ranking invalid:

- stable avoidance is dominated by off-track noncompletion;
- drift-required recovery lacks a staged recovery metric;
- hidden-dynamics robustness mixes task labels and failure modes;
- unavoidable mitigation is a severity-reduction task, not an obstacle-pass
  task.

The repair keeps four separate role surfaces. It does not collapse them into a
global success leaderboard.

## Design Principles

The repaired panel should enforce these rules:

1. Role surfaces are separate. A profile can be evaluated per role, but no
   profile can be globally ranked until each role-specific admissibility gate is
   passed.
2. Stable avoidance success is meaningful only after road-boundary admissibility
   is satisfied.
3. Drift-required recovery is a sequence of sub-events: drift/yaw authority,
   obstacle clearance, road retention, and post-maneuver recovery.
4. Hidden-dynamics robustness is evaluated within task label and hidden bucket,
   then summarized by worst bucket and spread. It is not a mixed-label average.
5. Unavoidable mitigation uses impact severity and collision mitigation, not
   obstacle-pass success.
6. Repairs must preserve the profile controls needed later for self-ID evidence:
   current-only, one-step, history windows, online GRU, and reset/ablation
   variants.

## Role-Specific Repairs

### stable_avoidance_aes

M1785 localized this role as pervasive off-track dominance:

```text
success_obstacle_pass_rate: 0.069444
collision_failure_rate: 0.013889
off_track_noncollision_noncompletion_rate: 0.916667
```

Repair:

- make road-boundary safety a first-class admissibility gate;
- split `success_obstacle_pass` from `road_boundary_retained`;
- add off-track severity summaries before ranking:
  `off_track_rate`, `off_track_overshoot_p50`, `off_track_overshoot_p90`,
  and `post_obstacle_recovery_in_corridor_rate`;
- rank stable AES only inside cells that are collision-low and off-track-low;
- preserve AEB-feasible and AES-feasible labels separately.

Metric-only repair:

- compute boundary-retention and off-track severity from existing episode rows
  where available.

Panel repair requiring new materialization:

- ensure stable AES cells are balanced by label (`aeb_feasible`,
  `aes_feasible`) and by hidden bucket;
- define a recovery horizon long enough to distinguish temporary evasive
  boundary excursions from unrecovered road departure.

### drift_required_recovery

M1785 localized this role as a controlled-recovery deficit:

```text
controlled_drift_recovery_success_rate: 0.027778
drift_used_rate: 0.333333
collision_failure_rate: 0.305556
off_track_noncollision_noncompletion_rate: 0.541667
```

Repair:

- decompose drift-required behavior into staged metrics:
  `drift_or_yaw_authority_used`, `obstacle_cleared`,
  `road_boundary_retained_or_recovered`, `post_maneuver_yaw_rate_bounded`,
  `post_maneuver_beta_bounded`, and `controlled_recovery`;
- record whether failure happens before obstacle clearance, during clearance,
  or during post-maneuver recovery;
- keep `drift_used_rate` diagnostic, not a primary success metric. Drift is a
  maneuver option, not the objective.

Metric-only repair:

- derive staged outcome flags from existing trajectory/episode metrics where
  present.

Panel repair requiring new materialization:

- include recovery horizon and recovery corridor in the spec;
- balance low-mu, tire-stiffness, and friction-step hidden buckets;
- avoid mixing drift-required cells with stable AES or unavoidable mitigation
  cells.

### hidden_dynamics_robustness

M1785 localized this role as label-mixed and failure-mode mixed:

```text
success_obstacle_pass_rate: 0.069444
collision_failure_rate: 0.430556
off_track_noncollision_noncompletion_rate: 0.500000
```

Repair:

- split robustness into task-label surfaces:
  `hidden_robust_aes_feasible`, `hidden_robust_drift_required`, and
  `hidden_robust_unavoidable_mitigation`;
- summarize within each label by hidden bucket:
  `worst_bucket_score`, `bucket_spread`, `collision_worst_bucket`,
  `off_track_worst_bucket`, and `impact_severity_worst_bucket` for mitigation;
- only compare profiles within the same task label and hidden bucket family.

Metric-only repair:

- compute hidden-bucket worst-case and spread from current scorecard rows.

Panel repair requiring new materialization:

- balance task labels inside each hidden bucket instead of allowing label mix to
  dominate the robustness aggregate;
- keep actuator delay, brake/drive variation, mass/CG shift, low-mu, tire
  stiffness, and friction-step as explicit hidden-bucket families.

### unavoidable_mitigation

M1785 localized this role as semantically separate from avoidance:

```text
impact_severity_proxy_mean: 17.470257
collision_failure_rate: 0.944444
off_track_noncollision_noncompletion_rate: 0.013889
```

Repair:

- keep mitigation in its own surface;
- primary metric: `impact_severity_proxy_mean` with lower better;
- supporting metrics:
  `impact_speed_proxy_mean`, `impact_beta_abs_mean`,
  `impact_yaw_rate_abs_mean`, `collision_mitigation_score_mean`,
  and `off_track_severity_proxy_mean`;
- never use obstacle-pass success as the primary mitigation metric.

Metric-only repair:

- compute severity by hidden bucket and profile from existing scorecard rows.

Panel repair requiring new materialization:

- balance unavoidable scenarios by impact geometry, speed, and hidden bucket;
- keep mitigation cells out of avoidance ranking.

## V2 Artifact Contract

The next materialization preflight should write these artifacts:

```text
summary.json
role_surface_contract.csv
metric_contract_v2.csv
admissibility_contract.csv
panel_repair_specs.json
panel_repair_matrix.csv
metric_only_repair_plan.csv
new_materialization_required.csv
claim_boundary.csv
```

Required contract columns:

```text
role_surface_id
task_label
hidden_bucket_family
primary_metric
primary_metric_direction
admissibility_gate
supporting_metrics
ranking_admissible_by_default
diagnostic_only_no_ranking_claim
requires_new_materialization
preserves_profile_controls
```

## Acceptance Rules

M1787 materialization preflight should pass only if:

- all four role surfaces are represented;
- stable AES has explicit road-boundary admissibility;
- drift-required recovery has staged outcome metrics;
- hidden robustness is split by task label and hidden bucket;
- unavoidable mitigation uses severity, not obstacle-pass success;
- all profile controls are preserved;
- no ranking is admitted by default;
- no reset, rollout, training, replay, PPO, private holdout, promotion, actor
  input change, profile tuning, paper-level claim, or level3 self-ID claim is
  made.

## Route Decision

Route to M1787 role-specific panel/metric repair materialization preflight.
M1787 should be no-rollout and should materialize only the v2 repair contract
and matrix. Reset feasibility or measured execution should not happen until the
repaired contract passes preflight.

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

- M1785 blockers can be mapped to concrete role-specific panel and metric
  repairs;
- a v2 no-rollout materialization preflight is admitted.

Unsupported:

- repaired panel execution;
- controller-family ranking;
- profile promotion;
- private-holdout evidence;
- paper-level benchmark evidence;
- level3 self-identification.
