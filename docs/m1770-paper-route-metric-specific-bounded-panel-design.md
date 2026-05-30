# M1770 Paper-Route Metric-Specific Bounded Panel Design

- status: completed
- decision: `admit_metric_specific_bounded_panel_materialization_preflight`
- parent synthesis: `docs/m1769-paper-route-task-quality-scenario-taxonomy-branch-synthesis.md`
- no rollout: true
- training/replay/PPO: false

## Purpose

M1770 designs a smaller role-separated public diagnostic panel after the full
M1764 taxonomy proved complete but too outcome-dominated for ranking. The goal
is not to choose the best controller family. The goal is to create a bounded
panel whose rows have clear metric semantics before any measured run.

The full taxonomy remains useful as a broad diagnostic corpus, but it mixes:

- ordinary/stable avoidance rows where off-track noncompletion dominates;
- drift-required rows where recovery matters;
- hidden-dynamics stress rows where collision and off-track failure have
  different meanings;
- unavoidable mitigation rows where collision may happen and impact severity is
  the primary metric.

Those roles should not be collapsed into one raw `success_obstacle_pass` score.

## Panel Shape

Design a `24`-spec bounded panel crossed with the existing `12` controller
profiles:

```text
4 role panels x 6 scenario specs x 12 profiles = 288 public diagnostic cells
```

This is small enough for repeated execution and large enough to keep the
profile controls meaningful.

The panel is public diagnostic evidence only. It is not a private holdout and
cannot support paper-level ranking until materialization, execution, outcome
quality, and ranking-admission audits pass.

## Role Panels

### A. Stable Avoidance / AES Panel

Scope:

```text
ordinary_stable_avoidance
aeb_infeasible_stable_aes
```

Primary metrics:

```text
avoidance_success
road_boundary_retention
off_track_violation
off_track_severity_proxy
recovery_success
recovery_time_proxy
```

Selection intent:

- include low-collision, off-track-dominated rows from M1767;
- include both center and offset obstacle buckets;
- avoid making the panel only wide-road or only nominal-road rows;
- include at least one stable-AES row where AEB alone is not enough.

Quality gates before ranking:

- metric completeness passes for every row;
- off-track dominance is reduced enough that profile differences are not
  drowned by road departure;
- collision remains low enough that off-track repair does not hide collisions;
- profile comparison remains blocked if one failure mode dominates most cells.

### B. Drift-Required Recovery Panel

Scope:

```text
drift_required_avoidance
```

Primary metrics:

```text
avoidance_success
controlled_drift_recovery_success
drift_used
high_sideslip_fraction
recovery_success
recovery_time_proxy
```

Selection intent:

- retain rows where drift can be useful but not mandatory by label injection;
- include both mild and hard lateral offsets;
- include at least one row where non-drift stable handling is plausible;
- keep high-sideslip behavior diagnostic, not directly rewarded in the panel
  design.

Quality gates before ranking:

- successful rows must show post-maneuver recovery evidence;
- drift use cannot be treated as success by itself;
- the panel must separate controlled drift from unrecovered spin/off-track.

### C. Hidden-Dynamics Robustness Panel

Scope:

```text
hidden_dynamics_stress
selected low_mu / friction_step / actuator_delay / tire_stiffness rows
```

Primary metrics:

```text
hidden_dynamics_robustness
avoidance_success
collision_failure
off_track_violation
impact_severity_proxy
```

Selection intent:

- cover at least low friction, friction step, actuator delay, and tire stiffness
  stress;
- avoid overrepresenting the M1767 dominant actuator-delay collision pocket;
- include matched current-frame/profile controls for later self-ID comparison;
- keep hidden parameters out of actor inputs.

Quality gates before ranking:

- hidden-dynamics buckets are balanced enough for interpretation;
- collision and off-track are reported separately;
- no hidden-dynamics bucket alone can determine the panel outcome.

### D. Unavoidable Mitigation Panel

Scope:

```text
unavoidable_mitigation
```

Primary metrics:

```text
collision_mitigation_score
impact_severity_proxy
impact_speed_proxy
impact_beta_abs
impact_yaw_rate_abs
off_track_severity_proxy
```

Selection intent:

- treat collision as expected in many rows, not as automatic panel failure;
- evaluate severity reduction and recoverability;
- include both very-close and close timing buckets;
- keep mitigation rows out of raw avoidance-success ranking.

Quality gates before ranking:

- impact/severity metrics are finite and applicable;
- raw obstacle pass is not used as the primary metric;
- profiles can be compared only after a mitigation-specific scoring audit.

## Selection Rules

M1771 materialization should use M1767 artifacts as source evidence but must not
select rows by best-performing profile.

Rules:

```text
1. Select scenario specs, not profile winners.
2. Cap each role panel at 6 scenario specs.
3. Cross every selected spec with all 12 existing profiles.
4. Preserve L1, L2 finite-window, L2 current-tiled, L3 online, and L3 reset controls.
5. Preserve actor input contract: no hidden parameters, labels, oracle feasibility, TTC, reference path, or controller mode in actor inputs.
6. Keep scenario labels metadata-only.
7. Keep unsupported fault modes explicitly out of covered claims.
```

Preferred source priority:

```text
M1767 target_dominant_slices
M1767 role/metric aggregates
M1743 semantics-aware specs
M1734 executable specs
M1764 seed-repair provenance
```

## No-Rollout Materialization Plan

M1771 should be a no-rollout materialization preflight. It should write:

```text
runs/m1771_metric_specific_bounded_panel_materialization_preflight/
  bounded_panel_specs.json
  bounded_panel_matrix.csv
  bounded_panel_role_summary.csv
  bounded_panel_metric_contract.json
  unsupported_feature_boundary.csv
  summary.json
```

Required M1771 checks:

```text
spec_count == 24
profile_count == 12
cell_count == 288
role_panel_count == 4
each role has 6 specs
each selected spec crosses all 12 profiles
labels_enter_actor_input == false
private_holdout_used == false
profile_specific_tuning == false
ranking_claim_made == false
unsupported_faults_treated_as_covered == false
```

M1771 must not run reset or policy rollout. Reset feasibility and measured
execution should be separate later milestones.

## Outcome-Quality Gates

The bounded panel can become comparison-ready only after later execution and
audit show:

```text
1. zero execution failures or explicit provenance for any repaired sampling row;
2. metric completeness passes for every applicable role;
3. no non-mitigation role is dominated by a single failure bucket above the pre-registered threshold;
4. mitigation rows are scored by severity/mitigation metrics, not obstacle pass;
5. controller-family ranking remains blocked until a dedicated ranking-admission audit.
```

Suggested initial thresholds for a later execution audit:

```text
non_mitigation_single_failure_dominance <= 0.75
mitigation_metric_finite_rate == 1.0
role_panel_min_episode_count == 72
all_selected_metrics_finite == true
guardrail_violation_count == 0
```

These thresholds are admission gates for panel quality, not driver-performance
claims.

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
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Claim Boundary

Supported:

- bounded metric-specific panel design;
- role-separated metric semantics;
- no-rollout materialization route;
- ranking remains blocked until panel-quality audits pass.

Unsupported:

- controller-family ranking;
- profile promotion;
- paper-level benchmark evidence;
- private-holdout evidence;
- level3 self-identification.

## Decision

Admit M1771 no-rollout bounded-panel materialization preflight.

M1771 should materialize the `24`-spec, `288`-cell panel and its metric contract
without running reset, policy rollout, training, profile tuning, ranking, or
paper-level claims.
