# M630 Trust-Projected Sequence Shape Implementation

## Purpose

M630 implements the no-training projected sequence candidate pass designed in
M629.

Question:

```text
Can radial projection and smoother sequence families recover any M627
trust-primary low/zero accepted sources without changing the trust limits?
```

Answer:

```text
Yes, but only narrowly. Projection preserves the trust limits and recovers one
zero-accepted source, but source diversity remains too small for optimizer
admission.
```

## Implementation

New module:

```text
src/autodrift/trust_projected_sequence_shape.py
```

Focused tests:

```text
tests/test_trust_projected_sequence_shape.py
```

The implementation adds:

```text
select_focused_source_rows
projected_sequence_scales
project_delta_sequence
build_projected_sequence_candidates
source_recovery_summary
run_trust_projected_sequence_shape
```

The source filter selects M627 near-miss source rows with:

```text
accepted_candidate_count <= 3
best_primary_failure in {mean_l2_excess, max_l2_excess}
has_collision_near_miss == false
```

Focused source ids:

```text
0
7
8
30
```

Projection scales raw delta sequences into the existing trust region:

```text
sequence_mean_l2 <= 0.08
sequence_max_l2 <= 0.10
max_delta_delta_l2 <= 0.08
```

The implementation uses a tiny inward numerical margin on projected scale so
that candidates do not fail due to floating-point boundary noise. This does not
change thresholds.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.trust_projected_sequence_shape \
  --checkpoint-policy bc5660=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --near-miss-sources runs/m627_near_miss_trust_geometry/near_miss_sources.csv \
  --near-miss-candidates runs/m627_near_miss_trust_geometry/near_miss_candidates.csv \
  --source-table runs/m616_expanded_sequence_source_miner/expanded_sequence_source_rows.csv \
  --surface-config fresh=configs/ppo_m541_matched_l3_variance_4096.json \
  --surface-config ood=configs/eval_m574_moderate_ood_l3.json \
  --sequence-lengths 3,5,7 \
  --run-dir runs/m630_trust_projected_sequence_shape
```

Artifacts:

```text
runs/m630_trust_projected_sequence_shape/projected_sequence_candidates.csv
runs/m630_trust_projected_sequence_shape/accepted_projected_sequences.csv
runs/m630_trust_projected_sequence_shape/unaccepted_projected_rows.csv
runs/m630_trust_projected_sequence_shape/source_recovery_summary.csv
runs/m630_trust_projected_sequence_shape/summary.json
```

## Results

Summary:

| Metric | Value |
| --- | ---: |
| focused source rows | `4` |
| focused source ids | `0, 7, 8, 30` |
| candidate rollouts | `7596` |
| accepted projected candidates | `9` |
| sources recovered by projection | `1` |
| recovered source ids | `30` |
| trust limits preserved | `true` |
| candidate margin improvement max | `0.021397` |
| accepted margin improvement mean | `0.020531` |
| accepted margin improvement min | `0.020135` |
| accepted margin improvement max | `0.021397` |

Accepted projected candidates:

| Family | Count |
| --- | ---: |
| projected_constant_delta | `8` |
| projected_decay_pulse | `1` |

Accepted candidates by source:

| Source | Count |
| ---: | ---: |
| `7` | `5` |
| `30` | `4` |

No accepted candidate violates the trust limits. The full candidate table also
preserves:

```text
max sequence_mean_l2: 0.0799999997
max sequence_max_l2: 0.0999999881
max max_delta_delta_l2: 0.0799999982
```

## Source Recovery

| Source | Before | After | Best improvement | Best family | Scale | Recovered |
| ---: | ---: | ---: | ---: | --- | ---: | --- |
| `30` | `0` | `4` | `0.021397` | projected_constant_delta | `0.742781` | true |
| `7` | `3` | `5` | `0.020817` | projected_constant_delta | `1.000000` | false |
| `8` | `0` | `0` | `0.018752` | projected_constant_delta | `0.970142` | false |
| `0` | `0` | `0` | `0.015290` | projected_constant_delta | `0.852802` | false |

M630 is therefore diagnostic-positive for projection feasibility, but still
diagnostic-negative for source-diverse optimizer admission.

## Interpretation

Projection is useful. It converts one zero-accepted trust-primary source
(`30`) into accepted projected candidates without relaxing the trust region.

The effect is narrow. Accepted projected candidates cover only:

```text
2 physical pairs
2 left seeds
2 surfaces
2 variants
1 target
```

Source `8` is close to the margin threshold after projection (`0.018752`), but
still below `0.02`. Source `0` remains farther away (`0.015290`). These should
be audited before choosing whether to add a targeted shape family or return to
source mining.

Do not train from M630 yet.

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
trust_projected_sequence_shape_implementation_pass_admit_audit
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
m631-trust-projected-sequence-shape-audit
```
