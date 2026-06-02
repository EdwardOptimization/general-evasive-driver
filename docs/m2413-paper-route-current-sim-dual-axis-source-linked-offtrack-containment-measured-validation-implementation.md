# M2413 Paper-Route Current-Sim Dual-Axis Source-Linked Offtrack Containment Measured Validation Implementation

- status: completed
- result_class: `current_sim_dual_axis_source_linked_offtrack_containment_measured_validation_pass`
- manifest: `experiments/manifests/m2413-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-measured-validation-implementation.json`
- design: `docs/m2412-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-measured-validation-design.md`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation.py`
- focused tests: `4 passed`
- summary: `runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/summary.json`
- repair execution/training/replay/PPO: `false`
- candidate/support/controller ranking and winner selection: `false`
- paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Implementation Result

M2413 implemented and ran the bounded source-linked measured-validation panel
frozen in M2412:

```text
unique reset targets: 350
selected checkpoints: 15
measured episodes: 5250
family membership rows: 18300
```

Execution passed the harness contract:

```text
episode_count: 5250
source_reset_target_count: 350
selected_checkpoint_count: 15
failure_count: 0
validation_failure_count: 0
metadata_missing_count: 0
metric_completeness_failure_count: 0
actor_contract_violation_count: 0
guardrail_violation_count: 0
ranking_admissible_count: 0
winner_selected: false
```

The runner writes one primary episode row per:

```text
reset_target_key + selected_checkpoint
```

and keeps overlapping source-linked family membership in a separate diagnostic
table:

```text
episode_family_membership_rows.csv
```

This prevents repeated source links from becoming an implicit family-ranking
weight.

## Output Artifacts

Primary artifacts:

```text
runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/summary.json
runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/episode_rows.csv
runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/episode_family_membership_rows.csv
runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/failure_rows.csv
runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/validation_failure_rows.csv
runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/metadata_missing_rows.csv
runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/metric_completeness_failures.csv
runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/claim_boundary.csv
runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/run_state.json
```

Diagnostic aggregates:

```text
aggregate_by_reset_target.csv
aggregate_by_pack.csv
aggregate_by_role_family.csv
aggregate_by_scenario_family.csv
aggregate_by_profile_seed.csv
aggregate_by_profile.csv
aggregate_by_obstacle_label.csv
aggregate_by_timing_bucket.csv
aggregate_by_lateral_bucket.csv
aggregate_by_hidden_dynamics_bucket.csv
aggregate_by_family_membership.csv
aggregate_by_family_profile.csv
aggregate_by_family_pack.csv
```

All aggregate tables are diagnostic-only:

```text
ranking_admissible: false
winner_selected: false
```

## Measured Outcome

The measured artifact is complete, but the driver outcome remains
offtrack-dominated:

```text
global role_success_rate: 0.06685714285714285
global collision_rate: 0.1761904761904762
global offtrack_rate: 0.7424761904761905
global max_step_noncompletion_rate: 0.008761904761904762
global other_failure_rate: 0.005714285714285714
dominant_failure_mode: offtrack_dominated_failure
mean_return: 18.455474321631854
mean_steps: 96.37485714285714
mean_min_clearance_margin: 6.963316190636537
min_min_clearance_margin: -0.34531212130133415
mean_max_off_track_overshoot: 0.05449152686016041
mean_time_to_first_off_track_s: 2.006145966709347
mean_high_sideslip_fraction: 0.10270575394649738
mean_action_rate: 0.005791724119690203
```

Outcome buckets:

```text
success_obstacle_pass: 342
collision_failure: 925
off_track_noncollision_noncompletion: 3898
max_steps_noncompletion: 46
speed_too_low_noncollision_noncompletion: 39
```

Role-success semantics count `351` successes globally, while raw
`success_obstacle_pass` contains `342` rows. M2414 should preserve this
semantic distinction when auditing outcomes.

Profile diagnostic slices:

```text
L0_current_masked: success_rate 0.05714285714285714, offtrack_rate 0.7876190476190477
L1_one_step: success_rate 0.05714285714285714, offtrack_rate 0.7942857142857143
L2_window_25: success_rate 0.05714285714285714, offtrack_rate 0.741904761904762
L2_window_50: success_rate 0.05714285714285714, offtrack_rate 0.7304761904761905
L3_online_gru: success_rate 0.10571428571428572, offtrack_rate 0.6580952380952381
```

These are not ranking claims. The selected-checkpoint panel is
diagnostic-only and M2413 does not implement the fair finite-window-vs-GRU
paper protocol.

## Contract Boundary

M2413 preserves the P0 actor input contract:

```text
actor_contract_id: P0_human_view_no_wheel_no_oracle
include_privileged_params: false
wheel_observation_mode: none
obstacle_relative_velocity_mode: zero
history_length: 1
```

No hidden dynamics, wheel/slip/tire/oracle, controller-mode, TTC, reference
trajectory, path-error, success/collision/progress, or other precomputed answer
enters actor input.

## Claim Boundary

Supported:

```text
M2413 completed a bounded 5250-episode source-linked measured-validation
artifact with clean metadata, metric completeness, actor contract, family
membership diagnostics, and guardrail checks.
```

Not supported:

```text
repair execution
scenario redesign executed
training repair success
candidate family ranking
support/controller ranking
winner selection
paper-level benchmark result
finite-window-vs-GRU conclusion
level3 self-identification
current-sim verdict
```

## Route Decision

Decision:

```text
source_linked_measured_validation_pass_route_to_result_audit
```

Next milestone:

```text
m2414-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-measured-validation-result-audit
```

M2414 should audit the M2413 measured artifact and decide whether the
offtrack-dominated outcome is actionable enough for localization,
consolidation, branch synthesis, or a stop/pivot. It must not rerun measured
validation, execute repair, train, rank families/profiles/controllers, or make
paper/current-sim/self-ID verdict claims.

## Failure Taxonomy

Observed:

```text
driver_outcome_failure: offtrack_dominated_failure
```

Not observed:

```text
scenario_sampling_failure
lineage_invalid
contract_violation
metric_artifact
behavior_regression
training_instability
objective_overfit
active config overwrite
repair execution
training repair success
candidate/profile/controller ranking
winner selection
```
