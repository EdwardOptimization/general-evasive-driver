# M1727 Paper-Route Task-Quality Scenario Taxonomy Design

- status: completed
- decision: `scenario_taxonomy_design_admit_no_rollout_preflight`
- parent synthesis: `docs/m1726-paper-route-controller-family-task-quality-repair-branch-synthesis.md`
- next manifest: `experiments/manifests/m1728-paper-route-task-quality-scenario-taxonomy-preflight.json`

## Summary

M1727 designs a scenario taxonomy to replace narrow public off-track repair with
structured task-quality distributions.

This milestone is design-only. It does not execute rollout, train, replay, run
PPO, promote, use private holdout, change actor inputs, tune profiles, rank
controller families, or claim paper-level evidence or level3 self-identification.

## Why This Taxonomy Is Needed

M1718-M1725 showed that local task-axis repair can reduce off-track dominance,
but the fixed public panel remains too dominated by road-boundary failures for
controller-family comparison. Continuing to adjust `track_width`, `finish`, or
`max_steps` on the same public panel would optimize a known public gate rather
than build a paper-quality evasive-driving benchmark.

The next branch should separate these questions:

```text
Can the driver avoid a normal obstacle?
Can it avoid when AEB alone is infeasible?
Can it use handling-limit or drift-like behavior when stable AES is insufficient?
Can it mitigate when collision is unavoidable?
Can it stay road-bounded without turning road departure into the only result?
Can it remain robust under hidden dynamics and component/fault stress?
```

## Scenario Families

M1728 should materialize exactly `72` scenario specs and `864` profile cells:

```text
6 scenario families
12 scenario specs per family
12 controller-family profiles per spec
864 total public diagnostic cells
```

| family id | scenario family | role |
| --- | --- | --- |
| `S1` | `ordinary_stable_avoidance` | Basic avoidable obstacle; both AEB and stable AES should often work. |
| `S2` | `aeb_infeasible_stable_aes` | Braking alone should be insufficient, but stable steering avoidance should be feasible. |
| `S3` | `drift_required_avoidance` | Stable steering envelope should be marginal; handling-limit yaw/drift behavior may be useful. |
| `S4` | `unavoidable_mitigation` | Full avoidance may be impossible; evaluate mitigation rather than binary success only. |
| `S5` | `off_track_boundary_stress` | Stress road-boundary behavior without letting off-track dominate every outcome. |
| `S6` | `hidden_dynamics_stress` | Stress friction, actuator, tire, brake/drive, mass/CG, and supported fault-like variations. |

These family labels are metadata for corpus construction, audit, and aggregate
reporting. They must not be added to actor observations.

## Per-Family Design

### S1 Ordinary Stable Avoidance

Purpose:

```text
Confirm the task distribution still contains normal avoidable cases.
```

Expected role:

```text
High obstacle completion should be possible without drift-like motion.
Failures here indicate basic task-quality or controller weakness, not
self-identification evidence.
```

### S2 AEB-Infeasible Stable AES

Purpose:

```text
Test cases where braking alone is too late or too weak, but a stable lateral
avoidance maneuver should work.
```

Required metadata:

```text
aeb_infeasible_public_diagnostic: true
stable_aes_expected_public_diagnostic: true
```

These are not actor inputs. They are used only for scenario construction and
audit.

### S3 Drift-Required Avoidance

Purpose:

```text
Represent handling-limit cases where stable steering is marginal and yawing the
vehicle may be useful.
```

The design should not force the policy to drift. It should make drift-like or
high-yaw behavior useful in some cases, while still allowing non-drift solutions
where the policy finds them.

### S4 Unavoidable Mitigation

Purpose:

```text
Avoid treating unavoidable collision as simple policy failure.
```

Audit should report mitigation metrics separately from success rate. If current
logging cannot yet measure impact speed, impact angle, or residual clearance
cleanly, M1728 must record those as missing instrumentation rather than invent a
proxy claim.

### S5 Off-Track Boundary Stress

Purpose:

```text
Keep road-bounded behavior in the task, but avoid a benchmark where every hard
case collapses into off_track_noncollision_noncompletion.
```

This family should vary road width, obstacle lateral offset, finish distance,
and max-step budget in a controlled way. It must not become another local repair
axis for the old public panel.

### S6 Hidden Dynamics Stress

Purpose:

```text
Stress the driver under dynamics uncertainty and fault-like variations.
```

Supported current stressors should include:

```text
friction level and friction step
brake_scale / drive_scale
tire_stiffness_scale
steering and drive actuator delay
mass / inertia / CG shift
sensor noise / sensor delay if supported by current env config
```

Fault-like scenarios should be represented carefully:

```text
single-wheel blowout or puncture
sudden wheel-specific grip loss
half-shaft / drive torque loss
brake-side imbalance
steering deadzone or partial actuator fault
```

If the current simulator cannot represent a fault faithfully, M1728 must write
it to `unsupported_scenario_features.csv`. Unsupported faults must not be
silently approximated and then reported as covered.

## M1728 No-Rollout Materialization Plan

M1728 should create these artifacts:

```text
runs/m1728_task_quality_scenario_taxonomy_preflight/summary.json
runs/m1728_task_quality_scenario_taxonomy_preflight/scenario_taxonomy.json
runs/m1728_task_quality_scenario_taxonomy_preflight/scenario_specs.csv
runs/m1728_task_quality_scenario_taxonomy_preflight/scenario_matrix.csv
runs/m1728_task_quality_scenario_taxonomy_preflight/contract_violations.csv
runs/m1728_task_quality_scenario_taxonomy_preflight/unsupported_scenario_features.csv
```

Required spec fields:

```text
scenario_spec_id
scenario_family_id
scenario_family
scenario_role
geometry_seed
dynamics_seed
obstacle_timing_bucket
obstacle_lateral_bucket
road_boundary_bucket
hidden_dynamics_bucket
env_config
contract_violation_count
environment_rollout_scheduled
profile_specific_tuning
```

Required matrix fields:

```text
scenario_workload_id
scenario_spec_id
scenario_family_id
scenario_family
profile_name
profile_config_path
checkpoint_path
config_exists
checkpoint_exists
environment_rollout_scheduled
training_scheduled
profile_specific_tuning
```

## Preflight Pass/Fail Checks

M1728 passes only if:

```text
scenario_family_count == 6
scenario_spec_count == 72
scenario_specs_per_family == 12 for every family
profile_count == 12
scenario_matrix_cell_count == 864
missing_config_count == 0
missing_checkpoint_count == 0
contract_violation_count == 0
environment_rollout_started == false
training_started == false
replay_started == false
ppo_used == false
promoted == false
private_holdout_used == false
actor_input_contract_changed == false
profile_specific_tuning == false
controller_family_ranking_claim_made == false
paper_level_claim_made == false
level3_self_id_claim_made == false
```

M1728 should fail or route to taxonomy repair if:

```text
any family has fewer than 12 specs
any family is omitted
scenario labels are inserted into actor observations
unsupported fault-like features are silently approximated
profile-specific tuning is introduced
the matrix is used to rank profiles before execution and audit
```

## Later Execution Metrics

The eventual measured execution should aggregate by:

```text
scenario_family
scenario_role
hidden_dynamics_bucket
road_boundary_bucket
obstacle_timing_bucket
profile_name
outcome_bucket
termination_reason
```

Core metrics:

```text
success_obstacle_pass_rate
collision_failure_rate
off_track_noncollision_noncompletion_rate
max_steps_noncompletion_rate
safe_noncollision_noncompletion_rate
clearance_margin_mean
clearance_margin_p10
return_mean
steps_mean
all_selected_metrics_finite
```

Mitigation metrics for S4 should be added only if instrumentation supports them
cleanly. Otherwise the audit must explicitly record missing instrumentation.

## Claim Boundary

Allowed after M1727:

```text
scenario taxonomy design is complete;
no-rollout taxonomy preflight is admitted;
the project has pivoted away from narrow public off-track repair.
```

Forbidden after M1727:

```text
controller-family ranking;
scenario execution result;
private-holdout generalization;
finite-window history necessity;
recurrent advantage;
paper-level evidence;
level3 self-identification.
```

## Decision

Admit M1728 no-rollout scenario taxonomy preflight. The next milestone may
implement materialization tooling, but must not execute environment rollout,
train, replay, run PPO, promote, use private holdout, change actor inputs, tune
profiles, or rank controller families.
