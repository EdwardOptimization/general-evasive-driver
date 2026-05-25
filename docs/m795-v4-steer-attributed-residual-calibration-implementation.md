# M795 V4 Steer-Attributed Residual Calibration Implementation

## Purpose

M795 implements and runs the no-PPO steer-attributed residual calibration
diagnostic designed by M794.

The question is:

```text
Can a deployable-feature steer/brake calibrator protect the active-source
normal margin while preserving enough intervention gap to beat the M786 alpha
0.15 reference?
```

This milestone is diagnostic only:

```text
no actor update
no residual-head update
no PPO
no checkpoint promotion
```

## Tooling Added

M795 extends:

```text
src/autodrift/v4_normal_margin_residual_calibration.py
tests/test_v4_normal_margin_residual_calibration.py
```

New objective mode:

```text
--objective-mode steer_attributed_gate
```

New calibrator:

```text
SteerAttributedResidualGate(feature) -> [g_steer, g_throttle, g_brake]

g_throttle = 0.0 fixed
learned outputs = [g_steer, g_brake]
```

Executed residual:

```text
delta_calibrated = [
  g_steer * delta_raw_steer,
  0.0,
  g_brake * delta_raw_brake
]

action = base_action + alpha * delta_calibrated
```

The M568 actor and M761 residual head remain frozen. Only the 2146-parameter
calibrator is trained.

## Command

Full run:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.v4_normal_margin_residual_calibration \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --residual-head runs/m761_v4_sequence_objective_probe/residual_head.pt \
  --positive-rows runs/m773_v4_broader_source_holdout_corpus_export/positive_sequence_outcomes.csv \
  --contrast-rows runs/m773_v4_broader_source_holdout_corpus_export/contrast_rows.csv \
  --scenario-config configs/extreme_fault_distribution_v4_broader_holdout_scenarios.json \
  --parent-replay-rows runs/m780_v4_broader_normal_boundary_alpha_probe/replay_rows.csv \
  --run-dir runs/m795_v4_steer_attributed_residual_calibration \
  --device cpu \
  --epochs 60 \
  --seed 7950 \
  --lr 0.001 \
  --alpha-train 0.2 \
  --objective-mode steer_attributed_gate \
  --initial-gate 0.85 \
  --gap-lift 0.003 \
  --active-normal-gate-max 0.50 \
  --intervention-gate-floor 0.75 \
  --alphas 0.0,0.125,0.15,0.2
```

## Artifacts

M795 writes:

```text
runs/m795_v4_steer_attributed_residual_calibration/summary.json
runs/m795_v4_steer_attributed_residual_calibration/alpha_metrics.csv
runs/m795_v4_steer_attributed_residual_calibration/gate_metrics.csv
runs/m795_v4_steer_attributed_residual_calibration/component_gate_metrics.csv
runs/m795_v4_steer_attributed_residual_calibration/active_source_metrics.csv
runs/m795_v4_steer_attributed_residual_calibration/training_metrics.csv
runs/m795_v4_steer_attributed_residual_calibration/calibration_metrics.csv
runs/m795_v4_steer_attributed_residual_calibration/replay_rows.csv
runs/m795_v4_steer_attributed_residual_calibration/objective_rows.csv
runs/m795_v4_steer_attributed_residual_calibration/rejected_rows.csv
runs/m795_v4_steer_attributed_residual_calibration/calibrator.pt
```

Summary:

```text
positive_rows: 2652
supported_positive_rows: 2640
reconstructed_rows: 2640
sample_reconstruction_success_rate: 0.995475
metadata_missing_rows: 0
rejected_rows: 12
replay_rows: 21120
objective_rows: 10560

candidate_alpha_count: 0
strong_candidate_alpha_count: 0
limited_candidate_alpha_count: 0
steer_component_selectivity_alpha_count: 0
result_class: v4_steer_attributed_calibration_component_collapse
```

Invariants:

```text
actor_backbone_changed: false
base_residual_head_changed: false
optimizer_updates_only_calibrator: true
ppo_used: false
promoted: false
```

## Alpha Results

| alpha | success | collision | gap mean | active margin | candidate |
| --- | ---: | ---: | ---: | ---: | --- |
| 0.0 | 1.000000 | 0.000000 | 0.040348 | 0.000124 | false |
| 0.125 | 1.000000 | 0.000000 | 0.042667 | 0.000049 | false |
| 0.15 | 1.000000 | 0.000000 | 0.043136 | 0.000034 | false |
| 0.2 | 1.000000 | 0.000000 | 0.044080 | 0.000004 | false |

M795 alpha `0.2` is informative:

```text
strict normal retention: pass
closed_loop_gap_pass: pass
gap mean: 0.044080
M780 alpha 0.125 gap reference: 0.044047
active-source margin: +0.000003618
M786 alpha 0.15 active margin reference: +0.000028246
```

So M795 fixes the collision that M761/M789 had at alpha `0.2`, but the active
source margin is too thin and below the registered M786 margin reference.

## Gate Behavior

Final aggregate gate behavior:

```text
normal steer gate mean:        0.680528
intervention steer gate mean:  0.683596
normal brake gate mean:        0.852762
intervention brake gate mean:  0.852612
throttle gate:                 fixed 0.0
```

Active-source gate behavior at alpha `0.2`:

```text
active normal steer gate mean:       0.668225
active intervention steer gate mean: 0.665187
active steer gate contrast:         -0.003038
```

This is the failure. The calibrator did not create the intended relation:

```text
active normal steer gate low
active intervention steer gate high
```

It learned a moderate steering gate and a high brake gate, with no meaningful
normal/intervention steering separation. That is a steer-attribution collapse,
even though throttle was correctly fixed to zero and brake stayed high.

## Interpretation

M795 supports:

```text
1. Steer-attributed gating can remove the alpha 0.2 active-source collision.

2. Fixed-zero throttle is not immediately catastrophic on the M773/M761
   diagnostic corpus.

3. Brake retention remains stable and does not cause the active-source
   collision.
```

M795 falsifies:

```text
1. The first steer-attributed objective is sufficient for a candidate.

2. A single deployable-feature steer gate with the current weights learns
   active normal versus intervention steering separation.

3. Alpha 0.2 is promotion-ready after removing the collision; active margin is
   still below the registered reference.
```

## Decision

M795 is a clean negative:

```text
v4_steer_attributed_calibration_component_collapse
```

It admits only an audit:

```text
next: m796-v4-steer-attributed-residual-calibration-audit
```

M796 should decide whether to design a stronger active-steer guard, add
active-source oversampling, add trajectory-time steering supervision, or stop
this residual-calibration branch.

PPO and checkpoint promotion remain blocked.
