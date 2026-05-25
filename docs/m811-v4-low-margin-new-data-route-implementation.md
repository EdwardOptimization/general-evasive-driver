# M811 V4 Low-Margin New Data Route Implementation

## Purpose

M811 implements and runs the no-training data route designed in M810.

The question is:

```text
Can active diagnostic warm-up plus joint obstacle/fault timing produce
source-diverse primary low-margin rows without weakening the alpha 0.2 and
0.00005 primary-margin gate?
```

This milestone is infrastructure-only:

```text
no actor training
no residual-head training
no optimizer
no PPO
no checkpoint promotion
```

## Implementation

New source:

```text
src/autodrift/v4_low_margin_new_data_route.py
```

New tests:

```text
tests/test_v4_low_margin_new_data_route.py
```

The implementation adds:

- source-balanced seed/fault/warm-up group generation;
- active warm-up modes: natural policy, steer pulse, brake tap, combined micro-probe;
- balanced fault variants over base fault, activation-step, and severity axes;
- source snapshot collection under frozen M568 actor plus frozen M761 residual head;
- boundary candidates over source axis, obstacle timing, obstacle lateral offset, and obstacle half-width;
- primary accepted-row export under `0.0 <= min_clearance_margin <= 0.00005`;
- source/axis balance summaries, margin-band diagnostics, checksum invariants, and current-model proxy-fault limitations.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_low_margin_new_data_route \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --residual-head runs/m761_v4_sequence_objective_probe/residual_head.pt \
  --scenario-config configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json \
  --run-dir runs/m811_v4_low_margin_new_data_route \
  --alpha 0.2 \
  --primary-margin-threshold 0.00005 \
  --collision-margin-floor -0.001 \
  --safe-margin-ceiling 0.01 \
  --diagnostic-safe-margin-ceiling 0.2 \
  --seed-count 12 \
  --max-base-faults 8 \
  --max-fault-specs 14 \
  --max-source-groups 96 \
  --max-snapshots-per-group 2 \
  --max-candidates-per-snapshot 14 \
  --min-rows 80 \
  --min-seeds 8 \
  --min-source-groups 16 \
  --min-source-indices 8 \
  --min-fault-pairs 4 \
  --min-warmup-modes 2 \
  --min-boundary-axes 3 \
  --max-seed-dominance 0.25 \
  --max-source-group-dominance 0.15 \
  --max-fault-pair-dominance 0.40 \
  --max-boundary-axis-dominance 0.60 \
  --device cpu
```

## Result

Run directory:

```text
runs/m811_v4_low_margin_new_data_route
```

Summary:

```text
result_class: v4_low_margin_new_data_route_sparse
fault_specs: 14
source_groups: 96
source_snapshots: 192
boundary_search_plan_rows: 2688
boundary_search_replay_rows: 2688
replay_errors: 0
warmup_artifact_rows: 0
accepted_primary_raw_rows: 0
accepted_primary_rows: 0
```

Margin bands:

```text
collision_negative: 542
primary_0_to_5e-5: 0
near_5e-5_to_1e-3: 0
near_1e-3_to_1e-2: 6
wide_1e-2_to_5e-2: 26
wide_over_5e-2: 2114
nonfinite: 0
```

Boundary-axis replay coverage:

```text
fault_activation_step: 60
fault_severity: 12
obstacle_half_width: 576
obstacle_lateral_offset: 1152
obstacle_timing: 768
source_state: 36
warmup_probe_mode: 84
```

Closest row to the primary target:

```text
margin: -0.0007608713848834547
distance_to_target: 0.0007858713848834547
seed: 78059
source_group_id: 83
source_index: 167
warmup_mode: natural_policy
fault_family_pair: drive_authority_drop->nominal
boundary_axis: obstacle_lateral_offset
plan_reason: source_group_lateral_offset
```

## Contract Checks

The run preserved the no-training and no-promotion invariants:

```text
actor_backbone_changed: false
residual_head_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
checkpoint_promoted: false
```

Checksums:

```text
base_actor_checksum_before: d9f636b495426c606140d15ddc207243979e87f1effbd89deb2946ae7c874c88
base_actor_checksum_after:  d9f636b495426c606140d15ddc207243979e87f1effbd89deb2946ae7c874c88
residual_head_checksum_before: 87f7bf7359ee0e23d5b388fa6759cc8056c6acf2a828797f70cb118ed44b4b94
residual_head_checksum_after:  87f7bf7359ee0e23d5b388fa6759cc8056c6acf2a828797f70cb118ed44b4b94
```

## Interpretation

M811 is a clean negative result.

It supports:

- the new route is runnable end to end;
- active warm-up did not create early warm-up artifacts in this run;
- source/fault/warm-up/boundary-axis replay coverage was generated;
- actor and residual head remained frozen;
- fixed obstacle/fault candidate deltas can create both collision-side and safe-side rows.

It falsifies:

- M811's current fixed candidate grid is sufficient to populate the strict primary low-margin window;
- active diagnostic warm-up plus fixed joint obstacle/fault timing is enough by itself to create source-diverse primary rows.

The key evidence is that `542` candidates collided and `2146` candidates were safe, but there were `0` rows in both `0.0..0.00005` and `0.00005..0.001`. The sampler is jumping over the useful boundary rather than resolving it.

## Decision

Classification:

```text
v4_low_margin_new_data_route_sparse
```

M811 does not admit residual calibration, PPO, or checkpoint promotion.

Next blocker:

```text
m812-v4-low-margin-new-data-route-audit
```

M812 should audit whether the right next step is adaptive closed-loop boundary bracketing around M811's collision/safe edges, rather than another fixed-grid data route.

## Verification

```text
python -m compileall -q src/autodrift/v4_low_margin_new_data_route.py tests/test_v4_low_margin_new_data_route.py
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_v4_low_margin_new_data_route.py
```

Result:

```text
4 passed
```
