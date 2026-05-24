# M633 Targeted Source-8 Projected Shape Implementation

## Purpose

M633 implements the source-8 targeted no-training projected shape search
designed in M632.

Question:

```text
Can a local source-8 projected shape search recover source 8 without changing
trust limits or thresholds, while keeping source 7 and source 30 sentinels safe?
```

Answer:

```text
It recovers source 8 and source 0, and improves source 30, but regresses source
7. This is a strong targeted diagnostic result, not optimizer-ready evidence.
```

## Implementation

New module:

```text
src/autodrift/targeted_projected_sequence_shape.py
```

Focused tests:

```text
tests/test_targeted_projected_sequence_shape.py
```

The implementation adds explicit source-id filtering and targeted projected
shape families:

```text
targeted_constant_delta
targeted_decay_hold
targeted_late_brake_hold
targeted_steer_build_brake_hold
targeted_smoothstep_hold
```

It reuses the existing no-training rollout path and the trust projection logic
from M630. No actor parameters are changed.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.targeted_projected_sequence_shape \
  --checkpoint-policy bc5660=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --source-table runs/m616_expanded_sequence_source_miner/expanded_sequence_source_rows.csv \
  --baseline-source-summary runs/m630_trust_projected_sequence_shape/source_recovery_summary.csv \
  --source-ids 8,0,7,30 \
  --primary-source-id 8 \
  --secondary-source-id 0 \
  --sentinel-source-ids 7,30 \
  --surface-config fresh=configs/ppo_m541_matched_l3_variance_4096.json \
  --surface-config ood=configs/eval_m574_moderate_ood_l3.json \
  --sequence-lengths 5,7,9 \
  --run-dir runs/m633_targeted_source8_projected_shape
```

Artifacts:

```text
runs/m633_targeted_source8_projected_shape/targeted_projected_candidates.csv
runs/m633_targeted_source8_projected_shape/accepted_targeted_sequences.csv
runs/m633_targeted_source8_projected_shape/source_recovery_summary.csv
runs/m633_targeted_source8_projected_shape/summary.json
```

## Results

Summary:

| Metric | Value |
| --- | ---: |
| candidate rollouts | `10080` |
| accepted targeted candidates | `1290` |
| source8 recovered | `true` |
| source8 best improvement | `0.026789` |
| source0 best improvement | `0.022995` |
| source7 regression | `true` |
| source30 regression | `false` |
| trust limits preserved | `true` |
| candidate margin improvement max | `0.029507` |
| accepted margin improvement mean | `0.022829` |

Accepted candidates by source:

| Source | Accepted candidates |
| ---: | ---: |
| `8` | `664` |
| `30` | `430` |
| `0` | `196` |
| `7` | `0` |

Accepted candidates by family:

| Family | Accepted candidates |
| --- | ---: |
| targeted_constant_delta | `353` |
| targeted_late_brake_hold | `348` |
| targeted_steer_build_brake_hold | `337` |
| targeted_decay_hold | `160` |
| targeted_smoothstep_hold | `92` |

## Source-Level Result

| Source | M630 accepted | M633 accepted | Best M633 improvement | Delta vs M630 | Status |
| ---: | ---: | ---: | ---: | ---: | --- |
| `8` | `0` | `664` | `0.026789` | `+0.008036` | recovered |
| `0` | `0` | `196` | `0.022995` | `+0.007705` | recovered |
| `30` | `4` | `430` | `0.029507` | `+0.008110` | preserved/improved |
| `7` | `5` | `0` | `0.019965` | `-0.000852` | regressed |

The source-8 local grid does what it was designed to do: it recovers source `8`
and also recovers source `0`. The cost is that source `7` drops just below the
threshold.

Top source-8 accepted row:

```text
family: targeted_constant_delta
K: 9
steer_delta: 0.00
throttle_delta: -0.08
brake_delta: 0.03
projection_scale: 0.936328
margin_improvement: 0.026789
```

Top source-7 row after targeting:

```text
family: targeted_decay_hold
K: 9
steer_delta: 0.06
throttle_delta: -0.07
brake_delta: 0.04
margin_improvement: 0.019965
accepted: false
```

Source `7` is only `0.000035` below threshold, so this looks like a local-grid
coverage problem rather than a fundamental conflict. It still must be audited
before any optimizer admission.

## Interpretation

M633 is a strong positive targeted diagnostic:

```text
source 8 recovered
source 0 recovered
source 30 preserved and improved
trust limits preserved
```

But it is not optimizer-ready:

```text
source 7 sentinel regressed
accepted targeted candidates cover only OOD surface
the result was produced by a source-specific local grid
```

The next step should audit whether source `7` can be preserved by merging the
M630 source-7 pattern back into the targeted grid, instead of treating M633 as
a training corpus.

## Contract Checks

```text
diagnostic_only: true
labels_enter_actor_input: false
actor_parameters_changed: false
ppo_used: false
promoted: false
optimizer_admission: false
target_acceptance_thresholds_changed: false
trust_regions_changed: false
```

## Decision

Decision:

```text
targeted_source8_projected_shape_implementation_pass_admit_audit
```

Blocked:

```text
optimizer admission
actor training
PPO
checkpoint promotion
trust-region widening
target-threshold lowering
```

Next branch:

```text
m634-targeted-source8-projected-shape-audit
```
