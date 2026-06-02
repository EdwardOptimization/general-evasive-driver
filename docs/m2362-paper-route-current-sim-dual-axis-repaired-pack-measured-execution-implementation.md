# M2362 Paper-Route Current-Sim Dual-Axis Repaired Pack Measured Execution Implementation

- status: completed
- result_class: `current_sim_dual_axis_repaired_pack_measured_execution_pass`
- manifest: `experiments/manifests/m2362-paper-route-current-sim-dual-axis-repaired-pack-measured-execution-implementation.json`
- summary: `runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/summary.json`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_repaired_pack_measured_execution.py`
- focused tests: `3 passed`
- measured execution in M2362: `true`
- policy action executed: `true`
- training/replay/PPO: `false`
- support-policy ranking claim made: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`
- scenario redesign executed claim made: `false`

## Execution Result

M2362 implements the pack-aware measured-execution runner and runs the frozen
M2361 panel:

```text
config_pack_count: 5
scenario_specs_per_pack_count: 72
pack_aware_scenario_spec_count: 360
unique_scenario_spec_id_count: 72
selected_checkpoint_count: 15
episode_count: 5400
failure_count: 0
validation_failure_count: 0
metadata_missing_count: 0
metric_completeness_failure_count: 0
guardrail_violation_count: 0
```

Pack/profile denominator:

```text
pack_counts:
  baseline_reference_pack: 1080
  g_primary_pack: 1080
  h_primary_pack: 1080
  g_h_primary_pack: 1080
  gh_minimal_pack: 1080

profile_counts:
  L0_current_masked: 1080
  L1_one_step: 1080
  L2_window_25: 1080
  L2_window_50: 1080
  L3_online_gru: 1080
```

## Outcome Artifact

M2362 records the measured outcome artifact but does not interpret it as a
ranking or paper result.

Global outcome:

```text
success_count: 352
success_rate: 0.06518518518518518
collision_count: 1078
collision_rate: 0.19962962962962963
offtrack_count: 3922
offtrack_rate: 0.7262962962962963
max_step_noncompletion_count: 32
other_failure_count: 16
dominant_failure_mode: offtrack_dominated_failure
mean_min_clearance_margin: 6.79116992686492
min_min_clearance_margin: -0.3747987476447765
```

Outcome rows:

```text
success_obstacle_pass: 342
collision_failure: 1078
off_track_noncollision_noncompletion: 3922
max_steps_noncompletion: 32
speed_too_low_noncollision_noncompletion: 26
```

M2363 must audit these outcomes before any repair, ranking, or paper-route
interpretation.

## Repair Metadata

Repair metadata is preserved in the measured artifact:

```text
repair_class_counts:
  no repair class: 4920
  timing_related: 405
  hidden_only: 45
  lateral_hidden: 30
```

These counts match the 32 repaired scenario rows multiplied by 15 selected
checkpoints.

## Artifacts

M2362 writes:

```text
runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/summary.json
runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/episode_rows.csv
runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/failure_rows.csv
runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/validation_failure_rows.csv
runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/metadata_missing_rows.csv
runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/metric_completeness_failures.csv
runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/claim_boundary.csv
runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/aggregate_by_pack.csv
runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/aggregate_by_pack_profile.csv
runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/aggregate_by_repair_class.csv
runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/aggregate_by_role_family.csv
runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/aggregate_by_scenario_family.csv
runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/aggregate_by_profile_seed.csv
runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/aggregate_by_profile.csv
runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/aggregate_by_obstacle_label.csv
runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/aggregate_by_timing_bucket.csv
runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/aggregate_by_lateral_bucket.csv
runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/aggregate_by_hidden_dynamics_bucket.csv
```

## Commands

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_paper_route_current_sim_dual_axis_repaired_pack_measured_execution.py
```

Result:

```text
3 passed in 2.08s
```

Frozen measured-execution command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.paper_route_current_sim_dual_axis_repaired_pack_measured_execution \
  --repaired-config-pack-manifest runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/repaired_config_pack_manifest.json \
  --selected-rows runs/m2262_paper_route_current_sim_midcourse_corridor_containment_training_execution/selected_checkpoint_rows.csv \
  --config-root runs/m2262_paper_route_current_sim_midcourse_corridor_containment_training_execution/configs \
  --output-dir runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution \
  --eval-seed-base 236200 \
  --target-pack-count 5 \
  --target-scenario-specs-per-pack 72 \
  --target-selected-checkpoint-count 15 \
  --target-episode-count 5400 \
  --device cpu \
  --no-resume \
  --next-blocker m2363-paper-route-current-sim-dual-axis-repaired-pack-measured-execution-result-audit
```

## Claim Boundary

M2362 may claim only:

```text
the frozen pack-aware measured-execution panel completed and produced complete
auditable outcome artifacts.
```

It does not support:

```text
support-policy ranking;
controller-family ranking;
winner selection;
paper-level benchmark evidence;
finite-window vs GRU conclusion;
level3 self-identification evidence;
scenario redesign executed.
```

## Decision

Decision:

```text
dual_axis_repaired_pack_measured_execution_pass_route_to_result_audit
```

M2363 should audit the M2362 outcome artifact before any repair, comparison, or
paper-route conclusion.
