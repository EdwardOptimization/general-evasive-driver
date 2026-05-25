# M804 V4 Low-Margin Boundary-Window Retarget Implementation

## Purpose

M804 implements and runs the no-training boundary-window retargeting step
designed in M803.

The question is:

```text
Can public closed-loop retarget axes fill the primary low-margin successful
non-collision window that M801 missed?
```

This milestone is implementation and diagnostic replay only:

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
src/autodrift/v4_low_margin_boundary_window_retarget.py
tests/test_v4_low_margin_boundary_window_retarget.py
```

The tool reads M801 reference replay rows, selects boundary anchors, creates
public retarget candidates, and reruns closed-loop candidates with the frozen
M568 actor and frozen M761 residual head.

Artifacts:

```text
runs/m804_v4_low_margin_boundary_window_retarget/boundary_anchor_rows.csv
runs/m804_v4_low_margin_boundary_window_retarget/retarget_plan_rows.csv
runs/m804_v4_low_margin_boundary_window_retarget/retarget_replay_rows.csv
runs/m804_v4_low_margin_boundary_window_retarget/accepted_low_margin_window_rows.csv
runs/m804_v4_low_margin_boundary_window_retarget/diagnostic_axis_summary.csv
runs/m804_v4_low_margin_boundary_window_retarget/progress.jsonl
runs/m804_v4_low_margin_boundary_window_retarget/summary.json
```

The first implementation attempt exposed a tooling issue: the retarget code
fed path-frame obstacle distance into the existing body-frame relocation API.
That made zero-like geometry retargets not preserve the original snapshot
geometry. The final run uses the obstacle's actual body-frame coordinates from
the snapshot environment before applying retarget deltas.

## Tests

```bash
python -m compileall -q src/autodrift/v4_low_margin_boundary_window_retarget.py tests/test_v4_low_margin_boundary_window_retarget.py
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_v4_low_margin_boundary_window_retarget.py
```

Result:

```text
3 passed
```

## Command

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

## Result

Summary:

```text
anchor_rows: 136
collision_edge_anchor_rows: 60
safe_edge_anchor_rows: 24
diagnostic_safe_anchor_rows: 52
retarget_plan_rows: 672
retarget_replay_rows: 672
reconstruction_failures: 0
accepted_low_margin_window_rows: 252
result_class: v4_low_margin_boundary_window_geometry_only_diagnostic
```

The run did create primary-window rows:

```text
accepted margin min: 0.000004953
accepted margin median: 0.000025013
accepted margin max: 0.000046264
```

But they are not source-diverse enough for the guard corpus:

```text
unique_accepted_seeds: 3
required: 8

unique_accepted_source_indices: 9
required: 8

unique_accepted_fault_family_pairs: 4
required: 4

max_accepted_seed_dominance: 0.428571
required <= 0.25

max_accepted_source_index_dominance: 0.142857
required <= 0.15

max_accepted_fault_pair_dominance: 0.714286
required <= 0.40
```

Axis diagnostics are decisive:

```text
obstacle_distance:
  candidate_rows: 420
  replay_rows: 420
  accepted_rows: 0

obstacle_half_width:
  candidate_rows: 252
  replay_rows: 252
  accepted_rows: 252
  unique seeds: 3
  unique source_index values: 9
  unique fault-family pairs: 4
  max seed dominance: 0.428571
  max source_index dominance: 0.142857
  max fault-pair dominance: 0.714286
```

Accepted rows by pool:

```text
collision_edge: 180
safe_edge: 72
diagnostic_safe: 0
```

Accepted rows by source intervention variant:

```text
zero_command_obs: 105
reset_hidden_each_step: 87
reset_hidden_then_normal: 60
```

Accepted rows by seed:

```text
78143: 108
78096: 72
78272: 72
```

Accepted rows by fault-family pair:

```text
front_lateral_authority_drop->combined_fault: 180
combined_fault->delay_noise_fault: 39
combined_fault->global_mu_drop: 21
combined_fault->brake_authority_drop: 12
```

The intervention branch remains behaviorally sensitive on accepted rows:

```text
intervention_success_rate: 0.0
intervention_collision_rate: 1.0
intervention margin min: -0.029230
intervention margin median: -0.002373
intervention margin max: -0.000175
```

This supports the local proof mechanism, but the source distribution is still
too concentrated and the retarget axis is geometry-only.

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

## Classification

M804 is:

```text
v4_low_margin_boundary_window_geometry_only_diagnostic
```

Failure taxonomy:

```text
scenario_sampling_failure
metric_artifact risk if accepted as pass
```

Rejected labels:

```text
not contract_violation
not training_instability
not proof_washout
not promotion_gate_failure
```

The run is a useful diagnostic positive, because it proves that the primary
margin window can be populated by legitimate closed-loop replay when obstacle
geometry is retargeted. It is not sufficient for calibration because the rows
come from one retarget axis and only three seeds.

## Supported Claims

M804 supports:

```text
1. The M801 gap is a real boundary-window targeting issue, not an impossible
   primary threshold.

2. Closed-loop obstacle-half-width retargeting can create primary-window rows
   without changing actor or residual parameters.

3. These rows preserve strong intervention sensitivity: accepted normal rows
   are successful while their source interventions collide.

4. The current implementation does not yet create a source-diverse or
   axis-diverse guard corpus.
```

## Falsified Claims

M804 falsifies:

```text
1. Simple obstacle-distance retargeting is sufficient to populate the primary
   low-margin window.

2. The M803 public retarget plan already yields a source-diverse guard corpus.

3. Active-steer calibration can resume from M804 without an audit.
```

## Next Blocker

```text
m805-v4-low-margin-boundary-window-retarget-audit
```

M805 should audit whether this geometry-only diagnostic can be used as a
limited guard-debug corpus, whether another source-diverse axis expansion is
justified, or whether the branch needs synthesis before more retargeting.
