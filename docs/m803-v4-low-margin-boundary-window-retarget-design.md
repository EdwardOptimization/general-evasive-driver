# M803 V4 Low-Margin Boundary-Window Retarget Design

## Purpose

M803 designs the next step after M802 audited M801 as a clean
diagnostic-band-only result.

The question is:

```text
How should M804 target the collision/success boundary window so that it can
produce source-diverse successful non-collision rows in the primary low-margin
band without relaxing the gate?
```

This milestone is design-only:

```text
no implementation
no source wave
no residual calibration
no actor update
no residual-head update
no PPO
no checkpoint promotion
```

## M801 Boundary Evidence

M801 already expanded v4 source coverage:

```text
sequence_outcome_critical_rows: 4825
unique_sequence_outcome_seeds: 108
unique_sequence_outcome_fault_family_pairs: 18
reference replay reconstructed_rows: 4805
```

The failure is narrower. On normal-history alpha `0.2` residual replay:

```text
rows: 4805
success rate: 0.987513
collision rate: 0.012487
```

Rows with margin `<= 0.001` are all collisions:

```text
row_count: 60
success: 0
collision: 60
unique seeds: 2
unique source_index values: 5
unique fault-family pairs: 1
margin range: -0.000572 to -0.000173
```

Those collision-side rows are concentrated in:

```text
seeds: 78096, 78143
source_index values: 166, 310, 1036, 1122, 1638
steps: 21, 24, 27, 36, 39
fault pair: front_lateral_authority_drop->combined_fault
preferred faults:
  front_blowout_grip_proxy_pre_emergency
  front_corner_suspension_proxy
wrong faults:
  rear_blowout_drive_grip_proxy_emergency
  stuck_caliper_brake_pull_proxy
```

The nearest successful collision-free rows are not in the primary window:

```text
successful non-collision rows with margin <= 0.01: 24
unique seeds: 1
unique source_index values: 4
unique fault-family pairs: 3
margin range: 0.005243 to 0.005768
```

Those safe-side rows are concentrated in:

```text
seed: 78272
source_index values: 397, 478, 907, 999
steps: 24, 27, 30, 33
fault pairs:
  combined_fault->brake_authority_drop
  combined_fault->delay_noise_fault
  combined_fault->global_mu_drop
preferred fault:
  loaded_vehicle_brake_fade_extreme
wrong faults:
  actuator_sensor_delay_extreme
  brake_fade_extreme_pre_emergency
  ice_patch_emergency_entry
  sensor_delay_authority_proxy
```

This is a boundary-window miss, not a reason to widen the primary threshold.
The current distribution jumps from slightly negative collision margins to
safe rows around `0.005 m`, leaving the required successful
`0.0 <= margin <= 0.00005` window empty.

## Design Principle

M804 should retarget the public scenario variables that define the boundary,
then rerun closed-loop replay. It must not post-process margins or count a
row as safe by changing only the metric after rollout.

Allowed retarget axes are public scenario or current-model fault axes:

```text
obstacle half width
obstacle longitudinal distance / timing
fault activation step
fault severity scale
nearby source continuation step
```

The actor is allowed to observe obstacle geometry through the existing
human-view frame. Therefore changing obstacle width or distance is a valid
public scenario retarget, as long as the modified geometry is used during the
closed-loop replay itself and is recorded in artifacts.

Residual alpha may be scanned only as a diagnostic to locate a boundary. The
accepted corpus remains fixed at:

```text
alpha == 0.2
branch == normal
success == true
collision == false
0.0 <= min_clearance_margin <= 0.00005
```

## M804 Pipeline

M804 should implement a no-training tool:

```text
src/autodrift/v4_low_margin_boundary_window_retarget.py
tests/test_v4_low_margin_boundary_window_retarget.py
```

The tool should read existing M801 artifacts:

```text
runs/m801_v4_low_margin_source_diverse_reference_replay/replay_rows.csv
runs/m801_v4_low_margin_refresh_corpus_export/positive_sequence_outcomes.csv
runs/m801_v4_low_margin_refresh_corpus_export/contrast_rows.csv
configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json
```

It should write:

```text
runs/m804_v4_low_margin_boundary_window_retarget/boundary_anchor_rows.csv
runs/m804_v4_low_margin_boundary_window_retarget/retarget_plan_rows.csv
runs/m804_v4_low_margin_boundary_window_retarget/retarget_replay_rows.csv
runs/m804_v4_low_margin_boundary_window_retarget/accepted_low_margin_window_rows.csv
runs/m804_v4_low_margin_boundary_window_retarget/diagnostic_axis_summary.csv
runs/m804_v4_low_margin_boundary_window_retarget/progress.jsonl
runs/m804_v4_low_margin_boundary_window_retarget/summary.json
docs/m804-v4-low-margin-boundary-window-retarget-implementation.md
```

### Stage 1: Anchor Extraction

Select two public anchor pools from M801 normal alpha `0.2` replay:

```text
collision_edge:
  branch == normal
  alpha == 0.2
  collision == true
  -0.001 <= min_clearance_margin < 0.0

safe_edge:
  branch == normal
  alpha == 0.2
  success == true
  collision == false
  0.0 < min_clearance_margin <= 0.01
```

The known M801 anchors above are the minimum starting point, not a pass
condition. If M804 only reproduces those same three seeds, it should be
classified as source-concentrated even if it creates primary-window rows.

M804 may also include wider diagnostic safe rows up to `0.2 m` only to choose
additional seeds and fault-family pairs for retarget attempts. Those rows do
not count as low-margin evidence unless the rerun lands inside the primary
window.

### Stage 2: Retarget Plan Generation

For each anchor, generate small deterministic public perturbations.

For collision-side anchors, loosen the scenario until it becomes barely safe:

```text
obstacle_half_width_delta: negative values around the collision penetration
obstacle_distance_delta: small positive values
fault_activation_step_delta: +1, +2, +3 where the fault occurs before boundary
fault_severity_scale_delta: small capability increase
source_step_delta: -1, 0, +1 if a neighboring snapshot exists
```

For safe-side anchors, tighten the scenario until it approaches collision:

```text
obstacle_half_width_delta: positive values up to the safe margin scale
obstacle_distance_delta: small negative values
fault_activation_step_delta: -1, -2, -3 where valid
fault_severity_scale_delta: small capability decrease
source_step_delta: -1, 0, +1 if a neighboring snapshot exists
```

Recommended initial bounds:

```text
abs(obstacle_half_width_delta) <= 0.010 m
abs(obstacle_distance_delta) <= 0.250 m
abs(fault_activation_step_delta) <= 3 steps
relative fault severity scale delta <= 0.08
source_step_delta in {-1, 0, +1}
```

After a bracket is found, bisection or ternary refinement should continue on
the active axis until either:

```text
0.0 <= min_clearance_margin <= 0.00005
```

or the axis bound is exhausted.

### Stage 3: Closed-Loop Replay

Every candidate must be rerun closed-loop with:

```text
checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
residual_head: runs/m761_v4_sequence_objective_probe/residual_head.pt
alpha: 0.2
branch: normal
same P0 human-view actor contract
```

No actor parameter, residual-head parameter, or calibrator parameter may change.
The modified obstacle geometry or fault specification must be present before
the replay starts, not applied to the metric afterward.

The tool should also run the paired intervention branch for accepted rows when
available so that the low-margin guard corpus remains tied to the
sequence-outcome self-identification branch instead of becoming pure geometry
mining.

### Stage 4: Acceptance and Diagnostics

Primary acceptance:

```text
accepted rows >= 80
unique seeds >= 8
unique source_index values >= 8
unique fault-family pairs >= 4
max single seed dominance <= 0.25
max single source_index dominance <= 0.15
max single fault-family-pair dominance <= 0.40
normal collision rate in accepted rows == 0.0
actor checksum unchanged
residual-head checksum unchanged
training_started == false
optimizer_started == false
ppo_used == false
promoted == false
```

Primary row definition remains:

```text
branch == normal
alpha == 0.2
success == true
collision == false
0.0 <= min_clearance_margin <= 0.00005
metadata complete
```

Axis diagnostics must be reported:

```text
unique retarget axes
max retarget-axis dominance
accepted rows by original anchor pool
accepted rows by retarget axis
accepted rows by perturbation magnitude bucket
```

If all accepted rows come from one retarget axis, especially obstacle
half-width, M804 should classify the result as:

```text
v4_low_margin_boundary_window_geometry_only_diagnostic
```

That result may still be useful for debugging the active-steer guard, but it
must be audited before any calibration milestone treats it as broad
source-diverse evidence.

## Progress and Sharding

M801 source generation took long enough that M804 must be resumable and
observable.

The implementation should support:

```text
--anchor-shard-index
--anchor-shard-count
--resume
--max-anchors
--max-candidates-per-anchor
```

It should append progress rows to:

```text
progress.jsonl
```

Each progress row should include:

```text
anchor_key
retarget_axis
candidate_index
status
margin
success
collision
elapsed_seconds
```

This prevents another long run from failing silently or writing only at the
end.

## Proposed M804 Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_low_margin_boundary_window_retarget \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --residual-head runs/m761_v4_sequence_objective_probe/residual_head.pt \
  --reference-replay-rows runs/m801_v4_low_margin_source_diverse_reference_replay/replay_rows.csv \
  --positive-rows runs/m801_v4_low_margin_refresh_corpus_export/positive_sequence_outcomes.csv \
  --contrast-rows runs/m801_v4_low_margin_refresh_corpus_export/contrast_rows.csv \
  --scenario-config configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json \
  --run-dir runs/m804_v4_low_margin_boundary_window_retarget \
  --alpha 0.2 \
  --primary-margin-threshold 0.00005 \
  --collision-margin-floor -0.001 \
  --safe-margin-ceiling 0.01 \
  --diagnostic-safe-margin-ceiling 0.2 \
  --min-rows 80 \
  --min-seeds 8 \
  --min-source-indices 8 \
  --min-fault-pairs 4 \
  --max-seed-dominance 0.25 \
  --max-source-index-dominance 0.15 \
  --max-fault-pair-dominance 0.40 \
  --device cpu
```

## Result Classes

M804 should use explicit result classes:

```text
v4_low_margin_boundary_window_pass
v4_low_margin_boundary_window_sparse
v4_low_margin_boundary_window_source_concentrated
v4_low_margin_boundary_window_geometry_only_diagnostic
v4_low_margin_boundary_window_contract_violation
v4_low_margin_boundary_window_replay_error
```

Only `v4_low_margin_boundary_window_pass` can admit an active-steer guard
calibration implementation. Other results require an audit first.

## Forbidden Shortcuts

M804 must not:

```text
widen the primary <=0.00005 m threshold
count collision rows as low-margin successes
post-process obstacle radius after rollout to change margin
use private holdout feedback
train the actor
train the M761 residual head
train a calibrator
run PPO
promote a checkpoint
claim true wheel-level faults from current single-track proxy data
```

## Supported Design Claim

M803 supports only this claim:

```text
The next highest-leverage step is targeted no-training boundary-window
retargeting around M801 collision and nearest-safe anchors.
```

It does not claim that low-margin rows exist, that active-steer calibration is
admitted, or that any driver checkpoint improved.

## Next Blocker

```text
m804-v4-low-margin-boundary-window-retarget-implementation
```

M804 should implement and run the no-training retarget tool. PPO, residual
calibration, actor mutation, residual-head mutation, and promotion remain
blocked until the source-diverse primary low-margin corpus exists and is
audited.
