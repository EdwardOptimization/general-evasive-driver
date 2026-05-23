# M319 M317-Family Protected Surface Refresh

M319 refreshes the protected proof surface around the M314/M316 family after
M318 classified protected key `9944|perturbed|28|28` as single-key window
saturation. No PPO, actor update, promotion, or actor-input change was
performed.

## Question

M319 asks whether the current family still has source-diverse protected
wrong-history outcome evidence away from the saturated old key.

The possible outcomes were:

- stale saturated singleton: refresh the surface and convert it into a
  source-diverse protected corpus;
- saturated protected family: redesign the protected gate as a distribution
  gate or add window-aware retention;
- wrong-history sensitivity loss: stop PPO and redesign the self-ID objective.

## Checkpoints

```text
m314_base       runs/m313_m307_to_m310_protected_key_bounded_interpolation/checkpoints/alpha_0_14.pt
m316_a0_0025    runs/m316_m314_to_repaired_protected_key_bounded_interpolation/checkpoints/alpha_0_0025.pt
m316_repaired   runs/m316_exact_repair_from_raw_s40_seed10096/candidate_checkpoint.pt
```

The public-gate base remains `m316_a0_0025`.

## Matched-Current Mining

Artifact:

```text
runs/m319_m317_family_matched_current_seed9520
```

Probe seeds:

```text
9520,9521,9522,9523
```

| Metric | Value |
| --- | ---: |
| Candidate pairs | 276465 |
| Accepted pairs | 2753 |
| Accepted physical pairs | 282 |
| Accepted left steps | 33 |
| Accepted obstacle buckets | 21 |
| Surface found | true |

The M317 family still has a large matched-current ambiguity pool under the
strict zero-obstacle-relvel profile.

## Direct Outcome Gate

Artifact:

```text
runs/m319_m317_family_outcome_seed9520
```

| Metric | Value |
| --- | ---: |
| Input pairs | 2753 |
| Outcome rows | 16518 |
| Outcome summary rows | 54 |

The direct outcome gate generated continuation rows for boundary relocation.

## Boundary Relocation

Artifact:

```text
runs/m319_m317_family_boundary_surface_seed9520
```

| Metric | Value |
| --- | ---: |
| Candidate pairs | 2753 |
| Boundary replay rows | 66745 |
| Accepted wrong-history rows | 180 |
| Accepted wrong-history pairs | 81 |
| Wrong-history success drops | 180 |
| Accepted reset rows | 3181 |
| Accepted zero-current rows | 3437 |
| Surface found | true |

## Robustness Gate

Artifact:

```text
runs/m319_m317_family_boundary_robustness_seed9520
```

| Gate metric | Observed | Threshold | Pass |
| --- | ---: | ---: | --- |
| accepted wrong rows | 180 | >= 40 | true |
| physical pairs | 13 | >= 10 | true |
| left steps | 8 | >= 5 | true |
| checkpoints | 3 | >= 3 | true |
| targets | 2 | >= 2 | true |
| margin buckets | 2 | >= 2 | true |
| success-drop fraction | 1.0 | >= 1.0 | true |
| max rows per pair fraction | 0.133333 | <= 0.25 | true |
| control accepted rows | 0 | <= 0 | true |

Accepted wrong-history row metrics:

| Metric | Value |
| --- | ---: |
| mean margin gap | 0.009568 |
| max margin gap | 0.013187 |
| mean normal margin | 0.005901 |
| min normal margin | 0.002493 |
| max normal margin | 0.010152 |

## Interpretation

M319 is positive. It shows the M317 family still has source-diverse
wrong-history outcome evidence far away from the saturated old protected key's
`0.2` normal-margin window.

This supports the M318 classification:

```text
9944 is a saturated diagnostic singleton, not evidence that self-ID proof has disappeared.
```

The old key should not be deleted or bypassed immediately, but another PPO
proposal should not be run until the refreshed surface is converted into
replay-aligned objective/proof corpora.

## Decision

Admit:

```text
m320-protected-surface-objective-replay-conversion
```

Decision:

```text
admit_m320_protected_surface_objective_replay_conversion
```
