# M1733 Paper-Route Task-Quality Scenario Taxonomy Sampling Repair Design

- status: completed
- decision: `scenario_taxonomy_sampling_repair_design_admit_reset_stress_preflight`
- parent audit: `docs/m1732-paper-route-task-quality-scenario-taxonomy-result-audit.md`
- failed execution: `runs/m1731_task_quality_scenario_taxonomy_execution/summary.json`

## Summary

M1733 designs a non-mutating repair route for the M1731 scenario sampling
failure. The repair target is not policy behavior, PPO, reward, actor inputs, or
controller-family profiles. The repair target is the scenario taxonomy sampling
layer: the obstacle label/filter combinations in M1728 must be made feasible
before another 864-cell policy rollout is attempted.

This milestone is design-only. It does not run rollout, train, replay, run PPO,
promote, use private holdout, change actor inputs, tune profiles, rank
controller families, treat unsupported faults as covered, or claim paper-level
evidence or level3 self-identification.

## M1731 Failure Target

M1731 failure distribution:

| scenario family | failed cells | repair priority |
| --- | ---: | --- |
| `aeb_infeasible_stable_aes` | `144` | primary |
| `off_track_boundary_stress` | `144` | primary |
| `hidden_dynamics_stress` | `144` | primary |
| `drift_required_avoidance` | `10` | secondary |

All S2, S5, and S6 specs failed across all profiles. This means the problem is
at scenario reset/filter feasibility, not profile-specific policy behavior.

## Repair Principles

M1734 must create new repaired artifacts. It must not mutate the M1728 artifacts
in place.

Allowed repair scope:

```text
obstacle distance_range
obstacle half_width_range
track_width / finish_pass_distance if needed for boundary-family semantics
speed_range inside env_config randomization where the current template supports it
mu / hidden-dynamics ranges only when needed to preserve family meaning
max_sample_attempts
scenario metadata describing repair source and repair delta
```

Forbidden repair scope:

```text
actor observation contract
controller profile configs
checkpoints
reward objectives
training / PPO / replay
private holdout
controller-family ranking
unsupported single-wheel / half-shaft / side-specific fault approximation
```

The repaired taxonomy should keep the original family meanings:

| family | required meaning |
| --- | --- |
| S1 `ordinary_stable_avoidance` | ordinary avoidable/stable baseline |
| S2 `aeb_infeasible_stable_aes` | AEB-infeasible but conventional stable steering can be feasible |
| S3 `drift_required_avoidance` | handling-limit avoidance where drift/yaw authority can matter |
| S4 `unavoidable_mitigation` | unavoidable or near-unavoidable mitigation |
| S5 `off_track_boundary_stress` | road-boundary stress without silently making every row off-track dominated |
| S6 `hidden_dynamics_stress` | supported hidden dynamics stress only |

If a family cannot satisfy its label/filter constraints after bounded repair, it
must be reported as unresolved rather than silently approximated.

## Reset-Stress Preflight Requirement

The next implementation milestone must be reset-only. It should materialize a
new run directory:

```text
runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/
```

Required artifacts:

```text
summary.json
repaired_scenario_specs.json
repaired_scenario_specs.csv
repaired_scenario_matrix.csv
sampling_repair_delta.csv
reset_stress_rows.csv
sampling_failure_rows.csv
label_distribution_by_spec.csv
label_distribution_by_family.csv
contract_violations.csv
unsupported_scenario_features.csv
```

`reset_stress_rows.csv` must cover the exact planned execution cells:

```text
72 repaired scenario specs x 12 controller-family profiles = 864 reset checks
eval_seed = M1731 eval seed convention unless a new seed base is explicitly documented
```

Each reset row should record at least:

```text
scenario_workload_id
scenario_spec_id
scenario_family
profile_name
eval_seed
reset_success
error_type
error_message
sampled_obstacle_label
initial_mu
speed_ref
obstacle_distance
obstacle_half_width
require_aeb_infeasible
allowed_labels_metadata_only
repair_variant_id
```

## Repair Search Strategy

M1734 should use a deterministic candidate search per failed scenario spec:

1. Start from the M1728 spec.
2. Increase `max_sample_attempts` for diagnostics, but do not treat this alone
   as sufficient unless reset-stress succeeds with reasonable runtime.
3. Search bounded geometry variants that preserve family meaning.
4. If geometry alone cannot repair a family, search bounded speed/mu variants
   within the supported dynamics model.
5. Pick the smallest repair delta that passes reset-stress for the planned
   execution seeds.
6. Record every chosen delta in `sampling_repair_delta.csv`.
7. Record unresolved specs in `sampling_failure_rows.csv`.

This is a feasibility repair, not task-performance tuning. M1734 must not choose
parameters based on controller success, collision rate, off-track rate, or
profile ranking.

## Pass Criteria for M1734

M1734 preflight passes only if:

```text
repaired_scenario_spec_count == 72
repaired_matrix_cell_count == 864
reset_stress_row_count == 864
reset_success_count == 864
sampling_failure_count == 0
contract_violation_count == 0
unsupported_scenario_feature_count == 5
silent_unsupported_approximation_count == 0
unsupported_faults_treated_as_covered == false
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

If M1734 fails, route to sampling repair audit, not execution. A repaired
taxonomy must prove reset feasibility before policy rollout.

## Decision

M1733 admits M1734 reset-stress sampling repair preflight. The branch remains in
process/infrastructure mode until reset feasibility is proven.
