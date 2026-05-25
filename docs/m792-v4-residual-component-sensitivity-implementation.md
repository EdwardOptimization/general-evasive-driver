# M792 V4 Residual Component Sensitivity Implementation

## Purpose

M792 implements and runs the no-training fixed-mask residual component
sensitivity probe designed by M791.

The question is:

```text
Which M761 residual action components create intervention benefit, and which
components create active-source normal collision risk?
```

This milestone is diagnostic only:

```text
no actor update
no residual-head update
no calibrator training
no PPO
no checkpoint promotion
```

## Implementation

M792 adds:

```text
src/autodrift/v4_residual_component_sensitivity.py
tests/test_v4_residual_component_sensitivity.py
```

The runner freezes:

```text
base actor: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
residual head: runs/m761_v4_sequence_objective_probe/residual_head.pt
```

It executes:

```text
base_action = frozen_actor(observation, hidden)
raw_delta = frozen_residual_head(feature)
masked_delta = mask * raw_delta
action = clamp(base_action + alpha * masked_delta, -1, 1)
```

Registered masks:

```text
none:             [0, 0, 0]
all:              [1, 1, 1]
steer_only:       [1, 0, 0]
throttle_only:    [0, 1, 0]
brake_only:       [0, 0, 1]
throttle_brake:   [0, 1, 1]  alias no_steer
steer_brake:      [1, 0, 1]  alias no_throttle
steer_throttle:   [1, 1, 0]  alias no_brake
```

Registered alpha ladder:

```text
0.0, 0.125, 0.15, 0.2
```

## Command

Full run:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.v4_residual_component_sensitivity \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --residual-head runs/m761_v4_sequence_objective_probe/residual_head.pt \
  --positive-rows runs/m773_v4_broader_source_holdout_corpus_export/positive_sequence_outcomes.csv \
  --contrast-rows runs/m773_v4_broader_source_holdout_corpus_export/contrast_rows.csv \
  --scenario-config configs/extreme_fault_distribution_v4_broader_holdout_scenarios.json \
  --run-dir runs/m792_v4_residual_component_sensitivity \
  --device cpu \
  --alphas 0.0,0.125,0.15,0.2
```

The full replay took about 35 minutes on CPU. A later workflow improvement
should add progress streaming or parallel replay for this class of diagnostic.

## Artifacts

M792 writes:

```text
runs/m792_v4_residual_component_sensitivity/summary.json
runs/m792_v4_residual_component_sensitivity/mask_alpha_metrics.csv
runs/m792_v4_residual_component_sensitivity/component_replay_rows.csv
runs/m792_v4_residual_component_sensitivity/component_objective_rows.csv
runs/m792_v4_residual_component_sensitivity/active_source_metrics.csv
runs/m792_v4_residual_component_sensitivity/component_role_metrics.csv
runs/m792_v4_residual_component_sensitivity/rejected_rows.csv
```

Summary:

```text
positive_rows: 2652
reconstructed_rows: 2640
sample_reconstruction_success_rate: 0.995475
metadata_missing_rows: 0
rejected_rows: 12
component_replay_rows: 168960
component_objective_rows: 84480
active_source_rows: 384
actionable_mask_count: 0
attribution_component_count: 2
attribution_components: steer, brake
result_class: v4_residual_component_sensitivity_attribution_found
```

Invariants:

```text
actor_backbone_changed: false
base_residual_head_changed: false
optimizer_started: false
training_started: false
ppo_used: false
promoted: false
```

## Key Metrics

At alpha `0.125`:

| mask | success | collision | gap mean | active margin |
| --- | ---: | ---: | ---: | ---: |
| none | 1.000000 | 0.000000 | 0.040348 | 0.000124 |
| all | 1.000000 | 0.000000 | 0.044047 | 0.000009 |
| steer_only | 1.000000 | 0.000000 | 0.042799 | 0.000017 |
| throttle_only | 1.000000 | 0.000000 | 0.040827 | 0.000120 |
| brake_only | 1.000000 | 0.000000 | 0.041191 | 0.000121 |
| throttle_brake | 1.000000 | 0.000000 | 0.041661 | 0.000117 |
| steer_brake | 1.000000 | 0.000000 | 0.043600 | 0.000014 |
| steer_throttle | 1.000000 | 0.000000 | 0.043253 | 0.000012 |

At alpha `0.2`:

| mask | success | collision | gap mean | active margin |
| --- | ---: | ---: | ---: | ---: |
| none | 1.000000 | 0.000000 | 0.040348 | 0.000124 |
| all | 0.995455 | 0.004545 | 0.046317 | -0.000062 |
| steer_only | 0.995455 | 0.004545 | 0.044286 | -0.000049 |
| throttle_only | 1.000000 | 0.000000 | 0.041170 | 0.000117 |
| brake_only | 1.000000 | 0.000000 | 0.041748 | 0.000119 |
| throttle_brake | 1.000000 | 0.000000 | 0.042545 | 0.000112 |
| steer_brake | 0.995455 | 0.004545 | 0.045579 | -0.000054 |
| steer_throttle | 0.995455 | 0.004545 | 0.045043 | -0.000057 |

## Component Roles

M792 identifies:

```text
steer:
  useful evidence: true
  harmful evidence: true

throttle:
  useful evidence: false
  harmful evidence: false

brake:
  useful evidence: true
  harmful evidence: false
```

Interpretation:

```text
The M761 residual intervention benefit is steer-dominant, but the active-source
normal collision is also steer-dominant. Brake has weaker useful signal without
causing the active-source normal collision. Throttle does not show meaningful
component evidence in this probe.
```

## Decision

M792 supports:

```text
1. Component attribution is necessary before another vector objective.
2. The active-source alpha 0.2 collision is primarily tied to steering residual.
3. A fixed no-steer mask is safe but loses too much intervention gap.
4. A fixed steer mask can increase gap but is unsafe at the active source.
```

M792 falsifies:

```text
1. A simple fixed residual component mask is enough to beat the M786 Pareto
   reference.
2. Throttle residual is a meaningful source of intervention lift or active
   collision risk in the M773/M761 diagnostic corpus.
3. Generic vector output dimension alone is the right next lever.
```

No mask is actionable:

```text
actionable_mask_count: 0
```

M792 therefore admits only an audit milestone:

```text
next: m793-v4-residual-component-sensitivity-audit
```

M793 should decide whether the next branch is steer-specific attenuation,
steer-normal-boundary calibration, a trajectory-time steering residual probe,
or stopping residual calibration and returning to corpus or architecture
evidence.
