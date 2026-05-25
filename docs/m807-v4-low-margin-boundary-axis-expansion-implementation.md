# M807 V4 Low-Margin Boundary-Axis Expansion Implementation

## Purpose

M807 implements and runs the no-training boundary-axis expansion designed in
M806.

The question is:

```text
Can lateral, source-step, fault-axis, and bracketed retargeting create a
source-diverse and axis-diverse primary low-margin normal corpus?
```

This milestone is diagnostic replay only:

```text
no actor update
no residual-head update
no calibrator training
no PPO
no checkpoint promotion
```

## Implementation

Added:

```text
src/autodrift/v4_low_margin_boundary_axis_expansion.py
tests/test_v4_low_margin_boundary_axis_expansion.py
```

The tool reuses the frozen M568 actor and frozen M761 residual head from M804,
but expands the retarget search over these public axes:

```text
obstacle_half_width
obstacle_lateral_offset
source_step_neighborhood
fault_activation_step
fault_severity
bracketed_obstacle_distance
bracketed_obstacle_half_width
```

For fault-axis rows, M807 creates modified `FaultSpec` values and collects
snapshots under those modified faults before replay. It does not mutate
metadata after rollout. Source-step neighborhood rows require an exact
snapshot at the target step; missing exact snapshots are counted as
reconstruction failures and are not accepted.

Artifacts:

```text
runs/m807_v4_low_margin_boundary_axis_expansion/axis_anchor_rows.csv
runs/m807_v4_low_margin_boundary_axis_expansion/axis_plan_rows.csv
runs/m807_v4_low_margin_boundary_axis_expansion/axis_replay_rows.csv
runs/m807_v4_low_margin_boundary_axis_expansion/accepted_axis_balanced_rows.csv
runs/m807_v4_low_margin_boundary_axis_expansion/rejected_axis_candidates.csv
runs/m807_v4_low_margin_boundary_axis_expansion/axis_balance_summary.csv
runs/m807_v4_low_margin_boundary_axis_expansion/source_balance_summary.csv
runs/m807_v4_low_margin_boundary_axis_expansion/bracket_trace_rows.csv
runs/m807_v4_low_margin_boundary_axis_expansion/progress.jsonl
runs/m807_v4_low_margin_boundary_axis_expansion/summary.json
```

## Tests

```bash
python -m compileall -q src/autodrift/v4_low_margin_boundary_axis_expansion.py tests/test_v4_low_margin_boundary_axis_expansion.py
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_v4_low_margin_boundary_axis_expansion.py
```

Result:

```text
4 passed
```

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_low_margin_boundary_axis_expansion \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --residual-head runs/m761_v4_sequence_objective_probe/residual_head.pt \
  --reference-replay-rows runs/m801_v4_low_margin_source_diverse_reference_replay/replay_rows.csv \
  --m804-replay-rows runs/m804_v4_low_margin_boundary_window_retarget/retarget_replay_rows.csv \
  --scenario-config configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json \
  --run-dir runs/m807_v4_low_margin_boundary_axis_expansion \
  --alpha 0.2 \
  --primary-margin-threshold 0.00005 \
  --collision-margin-floor -0.001 \
  --safe-margin-ceiling 0.01 \
  --diagnostic-safe-margin-ceiling 0.2 \
  --min-rows 80 \
  --min-seeds 8 \
  --min-source-indices 8 \
  --min-fault-pairs 4 \
  --min-retarget-axes 3 \
  --max-seed-dominance 0.25 \
  --max-source-index-dominance 0.15 \
  --max-fault-pair-dominance 0.40 \
  --max-axis-dominance 0.60 \
  --device cpu
```

## Result

Summary:

```text
anchor_rows: 136
collision_edge_anchor_rows: 60
safe_edge_anchor_rows: 24
diagnostic_safe_anchor_rows: 52
initial_plan_rows: 6240
axis_plan_rows: 7882
axis_replay_rows: 7882
reconstruction_failures: 589
accepted_axis_raw_rows: 252
accepted_axis_balanced_rows: 48
result_class: v4_low_margin_boundary_axis_expansion_geometry_only_diagnostic
```

M807 replayed all planned axis families:

```text
bracketed_obstacle_distance: 2276 reconstructed rows
bracketed_obstacle_half_width: 1504 reconstructed rows
obstacle_lateral_offset: 1360 reconstructed rows
fault_severity: 870 reconstructed rows
fault_activation_step: 804 reconstructed rows
obstacle_half_width: 252 reconstructed rows
source_step_neighborhood: 227 reconstructed rows
```

But the primary-window accepted rows still come from only one axis:

```text
obstacle_half_width:
  raw accepted rows: 252
  balanced accepted rows: 48

all other axes:
  raw accepted rows: 0
```

Raw accepted-row diversity:

```text
raw_unique_accepted_seeds: 3
required: 8

raw_unique_accepted_source_indices: 9
required: 8

raw_unique_accepted_fault_family_pairs: 4
required: 4

raw_unique_accepted_retarget_axes: 1
required: 3

raw_max_accepted_seed_dominance: 0.428571
required <= 0.25

raw_max_accepted_fault_pair_dominance: 0.714286
required <= 0.40

raw_max_accepted_retarget_axis_dominance: 1.0
required <= 0.60
```

Balanced export under the M806 caps contains only `48` rows because the per-axis
cap prevents one half-width axis from filling an 80-row corpus alone:

```text
unique_accepted_seeds: 3
unique_accepted_source_indices: 6
unique_accepted_fault_family_pairs: 3
unique_accepted_retarget_axes: 1
max_accepted_retarget_axis_dominance: 1.0
```

Nearest positive margins outside the accepted axis are above the primary
threshold:

```text
bracketed_obstacle_distance min positive margin: 0.000063175
bracketed_obstacle_half_width min positive margin: 0.000744491
fault_severity min positive margin: 0.000575566
source_step_neighborhood min positive margin: 0.005155853
fault_activation_step min positive margin: 0.011166531
obstacle_lateral_offset min positive margin: 0.021813194
```

So M807 does not show that lateral, source-step, or fault-axis retargeting can
populate the strict primary low-margin band under the current public anchors.

## Invariants

No training or promotion occurred:

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

The actor input contract remains unchanged:

```text
P0 human-view no-wheel 72-dim frame + online GRU hidden state
```

## Classification

M807 is:

```text
v4_low_margin_boundary_axis_expansion_geometry_only_diagnostic
```

Failure taxonomy:

```text
scenario_sampling_failure
metric_artifact risk if treated as a pass
```

Rejected labels:

```text
not contract_violation
not training_instability
not proof_washout
not promotion_gate_failure
```

## Supported Claims

M807 supports these claims:

1. The implementation can replay multiple public retarget axes under frozen
   actor and residual-head checksums.
2. The strict primary low-margin band is still reachable through
   obstacle-half-width retargeting.
3. The additional M806 axes do not create primary-window accepted rows in this
   run.
4. The existing half-width accepted rows remain too source-concentrated and
   axis-concentrated for active-steer calibration.

## Falsified Claims

M807 falsifies this working hypothesis for the current public anchors:

```text
Adding lateral, source-step, fault-axis, and bracketed retargeting is enough to
produce a source-diverse and axis-diverse primary low-margin corpus.
```

It does not falsify the broader driver/self-identification research goal. It
only says the current low-margin source-diverse corpus route remains blocked by
axis and source concentration.

## Next Blocker

M807 should be audited before another retargeting or calibration milestone:

```text
m808-v4-low-margin-boundary-axis-expansion-audit
```

The audit should decide whether this branch needs synthesis, whether the
M804/M807 half-width rows are only a limited debug corpus, or whether a new
data-generation route is needed before active-steer calibration can be fair.
