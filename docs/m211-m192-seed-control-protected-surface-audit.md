# M211 M192-Seed Control Protected Surface Audit

M211 repeats the current-family protected-surface refresh on the M192 probe
seeds. This controls whether the M210 failure was a fresh-seed/corpus issue or
a true loss of current-family wrong-history near-boundary evidence.

No PPO, actor update, or actor input change is run in this milestone.

## Checkpoints

```text
m199_5201  runs/ppo_m199_stage2_from_m197_seed5201/checkpoint.pt
m202_5206  runs/ppo_m202_stage4_from_m201_seed5206/checkpoint.pt
m204_5209  runs/ppo_m204_stage5_from_m202_seed5209/checkpoint.pt
```

M204 remains the current best retained checkpoint.

## Matched-Current Mining

Artifact:

```text
runs/m211_current_family_matched_current_seed9520
```

Probe seeds:

```text
9520,9521,9522,9523
```

| Metric | Value |
| --- | ---: |
| Candidate pairs | 276588 |
| Accepted pairs | 2853 |
| Accepted physical pairs | 305 |
| Accepted left steps | 31 |
| Accepted obstacle buckets | 19 |
| Surface found | true |

Accepted by target:

| Target | Rows |
| --- | ---: |
| future braking deceleration | 2376 |
| future lateral accel response | 230 |
| future yaw response | 247 |

## Direct Outcome Gate

Artifact:

```text
runs/m211_current_family_outcome_seed9520
```

The direct gate produced `17118` continuation rows. This is the snapshot source
for boundary relocation.

## Boundary Relocation

Artifact:

```text
runs/m211_current_family_boundary_surface_seed9520
```

| Metric | Value |
| --- | ---: |
| Candidate pairs | 2853 |
| Boundary replay rows | 70805 |
| Wrong-history rows | 14161 |
| Accepted wrong-history rows | 171 |
| Accepted wrong-history pairs | 109 |
| Wrong-history success drops | 171 |
| Accepted reset rows | 3170 |
| Accepted zero-current rows | 3543 |
| Surface found | true |

M211 recovers a current-family wrong-history surface on the M192 seeds. This
means the M210 failure was seed/corpus-specific, not proof that current-family
wrong-history evidence is gone.

## Robustness Gate

Artifact:

```text
runs/m211_current_family_boundary_robustness_seed9520
```

| Gate metric | Observed | Threshold | Pass |
| --- | ---: | ---: | --- |
| accepted wrong rows | 171 | >= 40 | true |
| physical pairs | 13 | >= 10 | true |
| left steps | 8 | >= 5 | true |
| checkpoints | 3 | >= 3 | true |
| targets | 2 | >= 2 | true |
| margin buckets | 2 | >= 2 | true |
| success-drop fraction | 1.0 | >= 1.0 | true |
| max rows per pair fraction | 0.140351 | <= 0.25 | true |
| control accepted rows | 0 | <= 0 | true |

Accepted wrong-history row metrics:

| Metric | Value |
| --- | ---: |
| mean margin gap | 0.008632 |
| max margin gap | 0.012319 |
| mean normal margin | 0.005944 |
| min normal margin | 0.002978 |
| max normal margin | 0.010652 |

Decision:

```text
admit_boundary_wrong_history_objective
```

## Decision

M211 is positive.

What it proves:

- the current M199/M202/M204 family can still produce fresh wrong-history
  near-boundary outcome evidence;
- M210's failure was seed/corpus-specific;
- the refreshed surface is source-diverse enough to support objective sanity.

What it does not prove:

- that a future PPO checkpoint will retain the surface;
- that objective optimization is safe;
- that M204 should be updated before replay-aligned objective sanity.

Next step:

```text
m212-current-family-boundary-objective-sanity
```

M212 should convert the M211 accepted rows into replay-aligned boundary-outcome
corpora, starting with the current-best M204 checkpoint, and run objective plus
replay sanity before any guarded actor update or PPO.
