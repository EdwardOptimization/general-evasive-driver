# M628 Near-Miss Trust Geometry Audit

## Purpose

M628 audits the M627 near-miss trust-geometry artifacts before choosing the
next branch.

Question:

```text
Do M624 near misses point to candidate-shape design, source re-mining, or
safety shaping?
```

Answer:

```text
The next branch should design projected or smoother sequence candidates that
stay inside the existing trust limits, focused on trust-primary low/zero
accepted sources. Collision-primary rows should remain a separate safety branch.
```

## Evidence

M627 artifacts:

```text
runs/m627_near_miss_trust_geometry/summary.json
runs/m627_near_miss_trust_geometry/near_miss_candidates.csv
runs/m627_near_miss_trust_geometry/near_miss_sources.csv
docs/m627-near-miss-trust-geometry-analyzer.md
```

## Candidate-Level Classification

M627 scans `22140` sequence candidates and finds `802` unaccepted-but-useful
near misses across `13` source rows.

Primary failures:

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

Interpretation:

```text
dominant blocker: mean/max action-sequence trust geometry
not dominant: delta-delta smoothness
separate branch: candidate collision
not observed: off-road or spin-out
```

## Source-Level Classification

M627 finds `13` near-miss source rows:

| Tier | Sources |
| --- | ---: |
| core_boundary | `6` |
| near_boundary | `3` |
| support_boundary | `4` |

However, high near-miss count alone does not solve source diversity. Several of
the strongest sources already have many accepted candidates:

| Source | Accepted candidates | Near misses | Best improvement | Primary failure |
| ---: | ---: | ---: | ---: | --- |
| `13` | `152` | `143` | `0.134949` | mean_l2_excess |
| `14` | `152` | `143` | `0.134949` | mean_l2_excess |
| `20` | `110` | `133` | `0.060126` | mean_l2_excess |
| `32` | `110` | `133` | `0.060126` | mean_l2_excess |
| `5` | `80` | `122` | `0.044031` | mean_l2_excess |

The useful diversity opportunity is in low/zero accepted sources:

| Source | Accepted candidates | Tier | Surface | Variant | Target | Near misses | Best improvement | Primary failure |
| ---: | ---: | --- | --- | --- | --- | ---: | ---: | --- |
| `30` | `0` | support_boundary | ood | wrong_matched_history | future_braking_deceleration | `12` | `0.030757` | mean_l2_excess |
| `7` | `3` | core_boundary | fresh | delayed_history | future_braking_deceleration | `32` | `0.025968` | mean_l2_excess |
| `0` | `0` | support_boundary | ood | delayed_history | future_braking_deceleration | `2` | `0.023657` | mean_l2_excess |
| `8` | `0` | core_boundary | ood | delayed_history | future_yaw_response | `7` | `0.022960` | mean_l2_excess |
| `1` | `0` | core_boundary | ood | delayed_history | future_yaw_response | `58` | `0.025914` | candidate_collision |
| `2` | `0` | core_boundary | ood | delayed_history | future_yaw_response | `1` | `0.021347` | candidate_collision |
| `15` | `0` | core_boundary | fresh | delayed_history | future_lateral_accel_response | `15` | `0.021143` | candidate_collision |
| `21` | `0` | core_boundary | fresh | wrong_matched_history | future_yaw_response | `1` | `0.020580` | candidate_collision |

Low/zero accepted source counts:

```text
low accepted sources with trust-primary best failure: 4
zero accepted sources with trust-primary best failure: 3
zero accepted sources with collision-primary best failure: 4
```

## Branch Decision

Do not go directly to optimizer training. The result is still diagnostic.

Do not widen trust regions. The near-miss candidates are useful precisely
because they show what would be possible near the existing boundary.

Do not choose source re-mining as the immediate next step. M627 already exposes
useful near misses across `13` source rows, including low/zero accepted rows.
The next question is whether candidate shapes can convert some of those rows
without changing limits.

Do not mix collision-primary rows into trust-region evidence. Collision-primary
rows require safety-aware candidate design later.

Admit a design-only next step:

```text
m629-trust-projected-sequence-shape-design
```

M629 should design a no-training projected/smoothed sequence candidate pass:

```text
input: M627 near_miss_sources and M624 sequence candidates
focus: trust-primary low/zero accepted rows such as sources 30, 7, 0, and 8
method: project or shape raw sequence candidates back inside existing limits
limits: mean L2 <= 0.08, max L2 <= 0.10, delta-delta L2 <= 0.08
blocked: training, PPO, promotion, optimizer admission, threshold relaxation
```

The projected candidate pass should report whether it recovers source-level
accepted diversity, not just candidate count.

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
near_miss_trust_geometry_audit_admit_projected_shape_design
```

Blocked:

```text
optimizer admission
actor training
PPO
checkpoint promotion
trust-region widening
target-threshold lowering
collision-primary rows as trust-only evidence
```

Next branch:

```text
m629-trust-projected-sequence-shape-design
```
