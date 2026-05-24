# M627 Near-Miss Trust Geometry Analyzer

## Purpose

M627 implements and runs the no-training analyzer designed in M626.

Question:

```text
Which existing constraints block the M624 candidates that are useful but not
accepted?
```

This is diagnostic-only:

```text
no training
no PPO
no checkpoint promotion
no optimizer admission
no trust-region relaxation
no target-threshold relaxation
```

## Command

```bash
PYTHONPATH=src python -m autodrift.near_miss_trust_geometry \
  --sequence-candidates runs/m624_longer_low_amplitude_sequence_miner/sequence_candidates.csv \
  --unaccepted-rows runs/m624_longer_low_amplitude_sequence_miner/unaccepted_rows.csv \
  --mean-l2-limit 0.08 \
  --max-l2-limit 0.10 \
  --delta-delta-l2-limit 0.08 \
  --min-margin-improvement 0.02 \
  --min-risk-improvement 0.05 \
  --run-dir runs/m627_near_miss_trust_geometry
```

Artifacts:

```text
runs/m627_near_miss_trust_geometry/near_miss_candidates.csv
runs/m627_near_miss_trust_geometry/near_miss_sources.csv
runs/m627_near_miss_trust_geometry/summary.json
```

## Results

| Metric | Value |
| --- | ---: |
| candidate rows scanned | `22140` |
| near-miss candidates | `802` |
| near-miss source rows | `13` |
| best margin improvement | `0.134949` |
| median mean L2 excess | `0.013808` |
| median max L2 excess | `0.007703` |
| median delta-delta excess | `0.000000` |

Near-miss sources by tier:

| Tier | Sources |
| --- | ---: |
| core_boundary | `6` |
| near_boundary | `3` |
| support_boundary | `4` |

Primary failure counts:

| Primary failure | Candidates |
| --- | ---: |
| mean_l2_excess | `542` |
| max_l2_excess | `185` |
| candidate_collision | `75` |

Constraint flags:

| Constraint flag | Candidates |
| --- | ---: |
| fails_mean_l2 | `580` |
| fails_max_l2 | `528` |
| fails_delta_delta_l2 | `6` |
| candidate_collision | `75` |
| candidate_off_road | `0` |
| candidate_spin_out | `0` |

Candidate families:

| Family | Near-miss candidates |
| --- | ---: |
| constant_delta | `546` |
| decay_pulse | `206` |
| steer_then_brake | `34` |
| brake_release_then_steer | `16` |

Sequence lengths:

| K | Near-miss candidates |
| ---: | ---: |
| `3` | `231` |
| `5` | `262` |
| `7` | `309` |

Variants:

| Variant | Near-miss candidates |
| --- | ---: |
| delayed_history | `656` |
| wrong_matched_history | `146` |

## Source-Level Pattern

Top source rows by best margin improvement:

| Source | Tier | Surface | Variant | Target | Near misses | Accepted candidates | Best family | K | Best improvement | Primary failure |
| ---: | --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | --- |
| `13` | support_boundary | fresh | delayed_history | future_yaw_response | `143` | `152` | constant_delta | `7` | `0.134949` | mean_l2_excess |
| `14` | support_boundary | fresh | delayed_history | future_yaw_response | `143` | `152` | constant_delta | `7` | `0.134949` | mean_l2_excess |
| `20` | near_boundary | ood | delayed_history | future_yaw_response | `133` | `110` | constant_delta | `7` | `0.060126` | mean_l2_excess |
| `32` | near_boundary | ood | wrong_matched_history | future_yaw_response | `133` | `110` | constant_delta | `7` | `0.060126` | mean_l2_excess |
| `5` | near_boundary | fresh | delayed_history | future_lateral_accel_response | `122` | `80` | constant_delta | `7` | `0.044031` | mean_l2_excess |
| `30` | support_boundary | ood | wrong_matched_history | future_braking_deceleration | `12` | `0` | constant_delta | `7` | `0.030757` | mean_l2_excess |
| `7` | core_boundary | fresh | delayed_history | future_braking_deceleration | `32` | `3` | constant_delta | `7` | `0.025968` | mean_l2_excess |
| `1` | core_boundary | ood | delayed_history | future_yaw_response | `58` | `0` | constant_delta | `3` | `0.025914` | candidate_collision |

The near-miss set is real and source-diverse enough to audit, but it is not
training-ready. Several high-count sources already have many accepted
candidates, so candidate count is still not source-level evidence.

## Interpretation

M627 supports three conclusions.

First, M624 did not fail because useful near misses are absent. There are
`802` unaccepted-but-useful candidates across `13` source rows.

Second, the dominant blocker is trust geometry, not off-road or spin safety.
Primary failures are mostly mean/max L2 excess. Delta-delta excess appears only
as a secondary flag in `6` candidates and is not the main blocker.

Third, collision is a separate branch. There are `75` collision-primary near
misses across `4` source rows, and those should not be fixed by widening the
sequence trust region.

This suggests the next audit should decide whether to design projected or
smoother candidate families that remain inside the existing trust region:

```text
normalize sequence mean L2 instead of widening 0.08
cap per-step max L2 instead of widening 0.10
prefer smoother low-amplitude K=7 shapes
separate collision-primary sources from trust-primary sources
```

Do not treat this as optimizer admission. M627 only classifies the blocker.

## Contract Checks

```text
actor_input_changed: false
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
near_miss_trust_geometry_analyzer_pass_admit_audit
```

Next blocker:

```text
m628-near-miss-trust-geometry-audit
```
