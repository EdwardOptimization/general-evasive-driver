# M701 Boundary Sensitivity-Scale Diagnostic Implementation

## Purpose

M701 implements and runs the no-training diagnostic designed in M700.

Question:

```text
Was M698 empty because the snapshot window and perturbation scales were too
conservative, or because the current fresh/ood scenario distribution does not
produce local terminal-boundary rows that depend on command-response history?
```

This milestone is diagnostic-only:

```text
no actor training
no objective actor update
no PPO
no checkpoint promotion
no actor-input change
```

## Implementation

M701 adds:

```text
src/autodrift/boundary_sensitivity_scale_diagnostic.py
tests/test_boundary_sensitivity_scale_diagnostic.py
```

The diagnostic wraps the M698 fresh sampler across a registered matrix:

```text
target_obstacle_distance: 2.0, 1.0, 0.0, -1.0
max_prepass_margin:      0.50, 1.00
scales:
  local:              steer 0.04, throttle 0.06, brake 0.06
  plausible:          steer 0.08, throttle 0.12, brake 0.12
  stress:             steer 0.12, throttle 0.20, brake 0.20
  unrealistic_probe:  steer 0.20, throttle 0.35, brake 0.35
```

Each scale uses half and full positive/negative deltas.

The implementation separates:

```text
fresh_source_positive:
  enough accepted rows, trajectory rows, history-action-critical rows, and
  source diversity

scale_sparse_*:
  accepted rows exist at a scale, but no variant reaches fresh_source_positive
```

This distinction matters because sparse or history-insensitive accepted rows do
not admit source-corpus export.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.boundary_sensitivity_scale_diagnostic \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --surface-config fresh=configs/ppo_m541_matched_l3_variance_4096.json \
  --surface-config ood=configs/eval_m574_moderate_ood_l3.json \
  --seed-start 30000 \
  --seed-count 512 \
  --target-obstacle-distance 2.0 \
  --target-obstacle-distance 1.0 \
  --target-obstacle-distance 0.0 \
  --target-obstacle-distance -1.0 \
  --max-prepass-margin 0.50 \
  --max-prepass-margin 1.00 \
  --scale local=0.04,0.06,0.06 \
  --scale plausible=0.08,0.12,0.12 \
  --scale stress=0.12,0.20,0.20 \
  --scale unrealistic_probe=0.20,0.35,0.35 \
  --snapshot-stride 3 \
  --max-snapshots-per-episode 8 \
  --max-continuation-steps 40 \
  --device cpu \
  --run-dir runs/m701_boundary_sensitivity_scale_diagnostic
```

## Artifacts

```text
runs/m701_boundary_sensitivity_scale_diagnostic/summary.json
runs/m701_boundary_sensitivity_scale_diagnostic/variant_summary.csv
runs/m701_boundary_sensitivity_scale_diagnostic/scale_summary.csv
runs/m701_boundary_sensitivity_scale_diagnostic/window_summary.csv
runs/m701_boundary_sensitivity_scale_diagnostic/accepted_rows.csv
runs/m701_boundary_sensitivity_scale_diagnostic/rejected_rows.csv
```

## Result Summary

Aggregate:

```text
variant_count:                    32
episodes_attempted:           16384
snapshots_collected:         129792
perturbation_evaluated_rows:  26112
accepted_rows:                   99
best_variant_accepted_rows:      14
best_margin_sensitivity_p95:      0.009688
best_risk_sensitivity_p95:        0.009688
result_class: scale_sparse_plausible
```

Cleanliness:

```text
actor_parameters_changed: false
training_started:         false
ppo_used:                 false
promoted:                 false
```

Source-positive counts:

```text
plausible_source_positive_variants:    0
stress_source_positive_variants:       0
unrealistic_source_positive_variants:  0
```

Accepted rows by scale:

```text
local:              0
plausible:         16
stress:            21
unrealistic_probe: 62
```

History-action-critical rows:

```text
local:              0
plausible:          0
stress:             0
unrealistic_probe:  0
```

## Scale Summary

```text
scale              variants accepted trajectory history-critical best_p95 result
local                     8        0          0                0 0.001834 fresh_surface_empty
plausible                 8       16         16                0 0.003627 history_insensitive
stress                    8       21         21                0 0.005645 history_insensitive
unrealistic_probe         8       62         62                0 0.009688 history_insensitive
```

Even the unrealistic probe does not reach the original `0.02` sensitivity
threshold at p95 and does not create history-action-critical rows.

## Window Summary

All target/window combinations show the same pattern:

```text
accepted rows exist only sparsely
trajectory_boundary_rows == accepted_rows
history_action_critical_rows == 0
result_classes include fresh_surface_empty and history_insensitive only
```

The best window is:

```text
target_obstacle_distance: 2.0
max_prepass_margin:      1.0
accepted_rows:           20
history_action_critical: 0
best_p95:                0.009688
```

Closer obstacle targets (`1.0`, `0.0`, `-1.0`) do not produce
history-action-critical rows either.

## Interpretation

M701 supports a narrow but important conclusion:

```text
The M698/M701 fresh/ood scenario distribution can produce sparse terminal
sensitivity under larger perturbations, but those rows are history-insensitive
and are not a self-identification source surface.
```

This means the branch should not continue by simply:

```text
lowering thresholds
increasing first-action perturbations again
exporting the sparse rows as training targets
starting objective actor update
starting PPO
```

The more likely blocker is scenario coverage. The current distribution does not
contain enough situations where the same current scene/ego state requires
different emergency behavior because hidden vehicle capability differs.

## Extreme Scenario Implication

The user raised the likely missing factor during this run:

```text
Maybe the project has not covered sufficiently extreme hidden-condition
scenarios, such as sudden loss of grip, tire failure, axle failure, or other
vehicle faults.
```

M701 is consistent with that hypothesis. Current fresh/ood configs mostly test
ordinary randomized vehicle/friction conditions. They do not yet create
structured hidden faults such as:

```text
split-mu or single-wheel grip collapse
sudden global/local friction drop
tire puncture / deflation proxy
brake fade, brake bias shift, or stuck caliper proxy
drive torque loss / half-shaft failure proxy
steering lag, deadzone, stiction, or partial steering authority loss
mass, center-of-gravity, or load-transfer shifts
sensor delay/noise/bias under emergency timing
```

Those hidden conditions should remain out of actor input. The actor should only
infer them through deployable ego response, actuator state, previous commands,
scene geometry, and recurrent history.

## Supported Claims

M701 supports:

```text
1. The boundary sensitivity-scale diagnostic implementation is runnable and
   writes complete aggregate and per-variant artifacts.

2. The actor checksum remains unchanged; no training, PPO, or promotion occurs.

3. Larger perturbation scales increase sparse trajectory-boundary rows, but not
   history-action-critical rows.

4. The current fresh/ood scenario distribution is not an objective-ready
   self-identification source distribution.

5. The next useful step is an audit and likely pivot to explicit extreme
   dynamics / fault scenario construction.
```

## Falsified Claims

M701 falsifies:

```text
1. M698 was empty only because the first-action perturbation scale was too
   small.

2. Moving the obstacle-distance target from 2.0 to 1.0, 0.0, or -1.0 is enough
   to expose history-critical rows.

3. A plausible-scale accepted row count alone is enough to admit corpus export.
```

M701 does not falsify:

```text
closed-loop self-identification as the project objective
```

because the tested scenario distribution may simply lack the hidden-condition
stressors needed to make online self-ID necessary.

## Failure Taxonomy

Primary:

```text
scenario_sampling_failure
```

Reason:

```text
The sampled scenario/window/scale distribution did not produce source-positive
history-action-critical rows.
```

Secondary:

```text
metric_artifact
```

Reason:

```text
Accepted rows exist, but they are sparse and history-insensitive; treating
them as self-ID evidence would overclaim a metric artifact.
```

Not classified as:

```text
training_instability:
  no training occurred

contract_violation:
  actor inputs were unchanged

proof_washout:
  actor parameters were unchanged
```

## Decision

M701 passes as an implementation milestone:

```text
boundary_sensitivity_scale_diagnostic_implementation_passed
```

but fails as a source-positive diagnostic:

```text
scale_sparse_plausible_not_source_positive
```

No objective design, actor update, PPO, or promotion is admitted.

## Next

M702 should audit M701 and synthesize the branch decision.

Expected direction:

```text
pivot from repeated fresh sampling / perturbation-scale tuning
to explicit extreme dynamics and fault scenario corpus design
```
