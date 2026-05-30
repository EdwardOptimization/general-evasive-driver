# M1729 Paper-Route Task-Quality Scenario Taxonomy Preflight Result Audit

- status: completed
- decision: `scenario_taxonomy_preflight_audit_admit_execution_design`
- audited artifact: `runs/m1728_task_quality_scenario_taxonomy_preflight/summary.json`
- audited unsupported report: `runs/m1728_task_quality_scenario_taxonomy_preflight/unsupported_scenario_features.csv`

## Audit Result

M1728 is a clean no-rollout scenario taxonomy preflight.

Preflight plumbing:

- result class: `task_quality_scenario_taxonomy_preflight_pass`
- scenario families: `6`
- scenario specs: `72`
- scenario specs per family: `12`
- profile count: `12`
- scenario matrix cells: `864`
- missing config/checkpoint count: `0/0`
- contract violation count: `0`
- guardrail violation count: `0`
- unsupported scenario feature count: `5`
- silent unsupported approximation count: `0`

This audit did not execute rollout, train, replay, run PPO, promote, use private
holdout, change actor inputs, tune profiles, rank controller families, or claim
paper-level evidence or level3 self-identification.

## Family Coverage

M1728 preserves balanced family coverage:

| scenario family | specs |
| --- | ---: |
| `ordinary_stable_avoidance` | `12` |
| `aeb_infeasible_stable_aes` | `12` |
| `drift_required_avoidance` | `12` |
| `unavoidable_mitigation` | `12` |
| `off_track_boundary_stress` | `12` |
| `hidden_dynamics_stress` | `12` |

This is clean enough for execution design. It is not execution evidence.

## Unsupported Feature Audit

M1728 records these fault-like features as unsupported:

```text
single_wheel_blowout_or_puncture
wheel_specific_grip_loss
half_shaft_or_single_side_drive_torque_loss
brake_side_imbalance
steering_deadzone_or_partial_actuator_fault
```

Audit result:

```text
unsupported_scenario_feature_count: 5
silent_unsupported_approximation_count: 0
```

This passes the M1727/M1728 rule: current simulation does not pretend to cover
faults the single-track model cannot represent. Later work may add higher
fidelity dynamics, but these unsupported rows cannot be counted as covered
scenario execution.

## Execution Design Requirements

M1730 may design measured execution, but it must preserve more metadata than the
`scenario_matrix.csv` carries directly. The runner must join
`scenario_matrix.csv` with `scenario_specs.json` by `scenario_spec_id` and copy
these fields into every episode row:

```text
scenario_family_id
scenario_family
scenario_role
obstacle_timing_bucket
obstacle_lateral_bucket
road_boundary_bucket
hidden_dynamics_bucket
template_source_family
allowed_labels_metadata_only
labels_enter_actor_input
```

Required execution aggregates should include:

```text
scenario_family_aggregate.csv
scenario_role_aggregate.csv
hidden_dynamics_bucket_aggregate.csv
road_boundary_bucket_aggregate.csv
obstacle_timing_bucket_aggregate.csv
outcome_aggregate.csv
termination_reason_aggregate.csv
profile_outcome_aggregate.csv
scenario_family_outcome_aggregate.csv
```

M1730 should also pre-register that unsupported fault-like rows remain
unsupported and must not be reinterpreted as covered by the M1728 execution.

## Interpretation Boundary

Supported:

- The scenario taxonomy materialization is clean.
- The taxonomy has balanced public family coverage.
- The execution design can proceed if it preserves scenario metadata and
  unsupported-feature boundaries.

Unsupported:

- scenario execution result
- controller-family ranking
- recurrent advantage
- finite-window history necessity
- private-holdout evidence
- paper-level evidence
- level3 self-identification

## Decision

M1729 passes as a process audit. Route to M1730 scenario taxonomy execution
design before measured rollout.
