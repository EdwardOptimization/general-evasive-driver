# M222 M219-Family Protected Surface Refresh

M222 refreshes the protected proof surface around the current retained
M217/M218/M219 family after M220 failed the single historical protected key.

No PPO, actor update, or actor input change is run in this milestone.

## Checkpoints

```text
m217_10054  runs/m217_m204_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10054/optimized_checkpoint.pt
m218_5214   runs/ppo_m218_guarded_from_m217_seed5214/checkpoint.pt
m219_5216   runs/ppo_m219_guarded_from_m217_seed5216/checkpoint.pt
```

M219 seed `5216` remains the current best retained checkpoint.

## Matched-Current Mining

Artifact:

```text
runs/m222_m219_family_matched_current_seed9520
```

Probe seeds:

```text
9520,9521,9522,9523
```

| Metric | Value |
| --- | ---: |
| Candidate pairs | 276273 |
| Accepted pairs | 2816 |
| Accepted physical pairs | 292 |
| Accepted left steps | 31 |
| Accepted obstacle buckets | 19 |
| Surface found | true |

The matched-current surface remains large for the M217/M218/M219 family.

## Direct Outcome Gate

Artifact:

```text
runs/m222_m219_family_outcome_seed9520
```

| Metric | Value |
| --- | ---: |
| Input pairs | 2816 |
| Outcome rows | 16896 |
| Outcome summary rows | 54 |

The direct outcome gate produced the continuation rows used by boundary
relocation.

## Boundary Relocation

Artifact:

```text
runs/m222_m219_family_boundary_surface_seed9520
```

| Metric | Value |
| --- | ---: |
| Candidate pairs | 2816 |
| Boundary replay rows | 69565 |
| Accepted wrong-history rows | 180 |
| Accepted wrong-history pairs | 107 |
| Wrong-history success drops | 180 |
| Accepted reset rows | 3203 |
| Accepted zero-current rows | 3576 |
| Surface found | true |

M222 recovers a multi-row wrong-history near-boundary surface for the current
retained family. This directly addresses the single-key fragility exposed by
M220.

## Robustness Gate

Artifact:

```text
runs/m222_m219_family_boundary_robustness_seed9520
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
| mean margin gap | 0.009100 |
| max margin gap | 0.012562 |
| mean normal margin | 0.006013 |
| min normal margin | 0.002757 |
| max normal margin | 0.010385 |

Decision:

```text
admit_boundary_wrong_history_objective
```

## Decision

M222 is positive.

What it proves:

- the current M217/M218/M219 retained family still has source-diverse
  wrong-history near-boundary outcome evidence;
- the M220 protected-key failure was single-key window fragility, not loss of
  current-family history evidence;
- the refreshed surface is diverse enough to support objective/replay sanity.

What it does not prove:

- that a future PPO checkpoint will retain the refreshed surface;
- that objective optimization is safe;
- that M219 should be updated before replay-aligned objective sanity.

Next step:

```text
m223-m219-family-boundary-objective-sanity
```

M223 should convert the M222 accepted rows into replay-aligned boundary-outcome
corpora, starting with the current-best M219 checkpoint, and run objective plus
replay sanity before any guarded actor update or PPO.
