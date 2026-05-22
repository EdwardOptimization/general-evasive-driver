# M266 M264-Family Protected Surface Refresh

M266 refreshes the protected proof surface around the current M261/M263/M264
family after M265 showed the historical protected key
`9944|perturbed|28|28` was saturated against the `0.2` normal-margin window.

No PPO, actor update, promotion, or actor-input change was performed.

## Question

M266 asks whether the old protected key is still representative of the current
family's proof boundary.

The possible outcomes were:

- stale saturated singleton: keep the old key as a diagnostic, but stop letting
  it alone veto PPO;
- saturated protected family: replace the single key with a distribution gate;
- wrong-history sensitivity loss: stop PPO and redesign the proof objective.

## Checkpoints

```text
m261_a001  runs/m261_m260_to_raw_interpolation/checkpoints/alpha_0_001.pt
m263_a005  runs/m263_m261_to_projection_interpolation/checkpoints/alpha_0_005.pt
m264_a001  runs/m264_m263_to_raw_interpolation/checkpoints/alpha_0_001.pt
```

The public-gate base remains `m264_a001`.

## Matched-Current Mining

Artifact:

```text
runs/m266_m264_family_matched_current_seed9520
```

Probe seeds:

```text
9520,9521,9522,9523
```

| Metric | Value |
| --- | ---: |
| Candidate pairs | 276609 |
| Accepted pairs | 2766 |
| Accepted physical pairs | 281 |
| Accepted left steps | 32 |
| Accepted obstacle buckets | 20 |
| Surface found | true |

The current family still has a large matched-current ambiguity pool under the
strict zero-obstacle-relvel profile.

## Direct Outcome Gate

Artifact:

```text
runs/m266_m264_family_outcome_seed9520
```

| Metric | Value |
| --- | ---: |
| Input pairs | 2766 |
| Outcome rows | 16596 |
| Outcome summary rows | 54 |

The direct outcome gate generated continuation rows for boundary relocation.

## Boundary Relocation

Artifact:

```text
runs/m266_m264_family_boundary_surface_seed9520
```

| Metric | Value |
| --- | ---: |
| Candidate pairs | 2766 |
| Boundary replay rows | 67725 |
| Accepted wrong-history rows | 180 |
| Accepted wrong-history pairs | 50 |
| Wrong-history success drops | 180 |
| Accepted reset rows | 3108 |
| Accepted zero-current rows | 3405 |
| Surface found | true |

The accepted rows are evenly present across the three current-family
checkpoints:

| Checkpoint | Accepted rows |
| --- | ---: |
| `m261_a001` | 60 |
| `m263_a005` | 60 |
| `m264_a001` | 60 |

Target coverage:

| Target | Accepted rows |
| --- | ---: |
| `future_braking_deceleration` | 168 |
| `future_yaw_response` | 12 |

## Robustness Gate

Artifact:

```text
runs/m266_m264_family_boundary_robustness_seed9520
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
| mean margin gap | 0.009323 |
| max margin gap | 0.012779 |
| mean normal margin | 0.005947 |
| min normal margin | 0.002616 |
| max normal margin | 0.010194 |

Decision:

```text
admit_boundary_wrong_history_objective
```

## Old-Key Representativeness

The old key remains useful, but M266 shows it is no longer representative as a
single hard veto for the current family:

- M265 old key at `m264_a001`: normal margin `0.199971`, slack `0.000029`;
- M266 refreshed accepted surface: mean normal margin `0.005947`, max
  `0.010194`;
- M266 wrong-history margin gaps remain positive and outcome-relevant, with all
  accepted wrong-history rows producing success drops.

This is not wrong-history sensitivity loss. It is single-key window saturation.

## Decision

M266 is positive.

What it proves:

- the current M261/M263/M264 family still has source-diverse near-boundary
  wrong-history outcome evidence;
- the old protected key is a saturated diagnostic singleton, not the whole
  current-family protected surface;
- PPO should remain blocked until this refreshed surface is converted into
  replay-aligned objective/proof corpora.

What it does not prove:

- that a future PPO checkpoint will retain the refreshed surface;
- that objective optimization on this surface is safe;
- that the old protected key should be deleted or loosened.

Next step:

```text
m267-protected-surface-objective-replay-conversion
```

M267 should convert the M266 accepted rows into source-diverse boundary-outcome
corpora and run objective plus replay sanity before any actor update or PPO.
The old protected key should stay as a diagnostic row, but it should not remain
the only hard protected-surface veto.
