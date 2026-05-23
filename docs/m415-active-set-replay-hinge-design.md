# M415 Active-Set Replay Hinge Design

M415 is a design milestone. It does not run PPO, promote a checkpoint, lower
thresholds, or change actor inputs.

## Why Scalar Anchors Are Not Enough

M411 and M414 bracketed the tradeoff:

| Candidate | Proof | Utility |
| --- | --- | --- |
| global `1e13` replay anchor | passes M267/M264, old-key, M183/M170 | retains only `5.8%` of M406 recovery improvement |
| source-weighted M414 | fails M267/M264 and old-key | retains `23.0%` of M406 recovery improvement |

This means the remaining problem is not a single global coefficient. The
residual needs to know which rows and branches are actually active failures.

## Active Set

M414 failed M267/M264 on two current-family rows:

| Corpus | Row | Branch | Failure |
| --- | ---: | --- | --- |
| M267/M264 | `6` | wrong-history | wrong-history success, margin `+0.000280` |
| M267/M264 | `15` | wrong-history | wrong-history success, margin `+0.000221` |

M414 failed old-key compact on two cases:

| Corpus | Case | Branch | Failure |
| --- | --- | --- | --- |
| old-key | `10004|perturbed|31|31|9.500000|-1.000000|0.800000` | wrong-history | wrong-history margin `+0.000324` |
| old-key | `9998|perturbed|25|25|11.000000|-1.000000|1.400000` | wrong-history | wrong-history margin `+0.000398` |

The previous M411 `1e12` boundary also failed:

```text
10023|perturbed|12|12|11.000000|-0.800000|1.200000
```

M416 should include that old-key case as a guard row even though M414 repaired
it.

## Hinge Residual

The new trajectory anchor should support a per-row action-distance radius:

```text
distance = ||tanh(policy_mean(obs, hidden)) - reference_action||_2
loss = weight * relu(distance - radius)^2
```

Interpretation:

- active failure rows get `radius = 0` or a very small radius;
- replay-safe rows get a nonzero radius so useful movement is not penalized;
- rows with large closed-loop margin slack can be omitted or assigned low
  weight;
- replay labels remain training-only residual metadata and are not actor inputs.

This differs from the current MSE anchor:

```text
loss = weight * mean((action - reference_action)^2)
```

The current MSE anchor penalizes every action movement, even if the row remains
safe. That caused M411's retention-heavy collapse.

## Proposed M416 Implementation

M416 should implement infrastructure only:

1. Extend the trajectory anchor NPZ schema with optional `radius`.
2. Load missing `radius` as zeros for backward compatibility.
3. Add `exact_trajectory_action_hinge_anchor_loss`.
4. Expose it through `exact_post_ppo_repair`, either by replacing the existing
   trajectory loss when `radius` exists or through an explicit CLI flag.
5. Add focused tests:
   - zero radius matches tight anchoring behavior;
   - positive radius produces zero loss inside the radius;
   - missing radius remains backward compatible.
6. Export an active-set hinge anchor artifact for the rows listed above.
7. Run a no-update exact repair smoke only.

M416 should not run the actual proof probe. The first proof probe should be
M417 after the loader/loss path is validated.

## Proposed Acceptance For M417

M417 should use the M416 active-set hinge anchor from the same M403 alpha `0.1`
raw proposal and require:

```text
exact M297/M270/old-key no-regression
M267/M264 first replay: 17 / 17
old-key compact replay: 0 accepted regressions
M183/M170 first replay: 17 / 17
recovery improvement retained vs M406 >= 0.20
```

If it passes proof but recovery retention is below `0.20`, classify it as
retention-heavy. If it retains recovery but fails proof, inspect active rows
before adding more scalar pressure.

## Decision

Admit:

```text
m416-active-set-hinge-anchor-implementation
```
