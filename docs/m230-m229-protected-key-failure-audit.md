# M230 M229 Protected-Key Failure Audit

M230 audits why M229 restored replay retention but still failed the historical
protected key. No PPO is run in this milestone.

Actor inputs are unchanged.

## Finding

M229 is not an old replay washout:

| Gate | M229 result |
| --- | ---: |
| M183 M168 replay | 16 / 16 drops retained |
| M183 M170 replay | 17 / 17 drops retained |
| M193 M189 replay | 14 / 14 drops retained |
| M212 M204 replay | 17 / 17 drops retained |
| M223 M219 replay | 17 / 17 drops retained |

M229 is also not broad behavior collapse:

| Seed | Success | Reset success | Zero-all success |
| ---: | ---: | ---: | ---: |
| 9505 | 0.8625 | 0.8500 | 0.8000 |
| 9506 | 0.8625 | 0.8500 | 0.8000 |

The remaining failure is specific to the protected key:

| Policy | Accepted | Normal margin | Wrong-history margin | Margin gap |
| --- | ---: | ---: | ---: | ---: |
| m224_10063 | 1 / 1 | 0.186385 | 0.086925 | 0.099460 |
| m226_5218 | 0 / 1 | 0.203847 | 0.104163 | 0.099684 |
| m229_5219 | 0 / 1 | 0.205200 | 0.106179 | 0.099021 |

M229 preserves a strong margin gap, but the normal-history margin leaves the
near-boundary window:

```text
0.205200 > 0.2
```

## Coverage Audit

The M229 PPO snippet anchor used the M223 M219 corpus:

```text
runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.npz
```

That corpus has 17 rows, all from M219-family seeds such as:

```text
9530, 9537, 9542, 9549, 9550, 9561
```

The protected key is:

```text
9944|perturbed|28|28
```

So the key itself is not in the snippet anchor surface.

The nearest M223 geometry row to the protected-key geometry
`x=11.0, y=-1.0, half_width=0.9` is still not the same row:

| M223 row | Seeds | Steps | Geometry | Distance |
| ---: | --- | --- | --- | ---: |
| 7 | 9530:9550 | 15:18 | x=11.340892, y=-0.575417, half_width=0.725522 | 0.571770 |

This explains the M229 result: the new snippet anchor keeps the model close to
M224 on the M223 proof surface, but it does not constrain the historical 9944
protected key.

The training log supports this:

```text
snippet_action_anchor_loss_mean = 1.900874e-08
```

The anchor was nearly perfectly satisfied on M223 snippets, yet the protected
key still failed.

## Diagnosis

M229 fixed the wrong failure mode for the protected key.

It fixed replay-surface action drift, which is why M183 M170 recovered from
M226's `16/17` to `17/17`. But the protected key is a separate historical
single-key surface, not included in M223 snippet anchoring.

Failure taxonomy:

```text
protected_key_window_failure
promotion_gate_failure
```

This does not justify loosening the protected-key threshold. It also does not
justify training lower clearance just to satisfy one key. The correct next step
is to make the protected-key evidence explicit as a surface, then decide whether
it should be anchored or refreshed.

## Decision

M229 remains rejected.

Current best remains:

```text
runs/m224_m219_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10063/optimized_checkpoint.pt
```

## Next Step

Pre-register M231:

```text
m231-protected-key-snippet-surface-export
```

M231 should export a deployable snippet/action-anchor surface for the protected
key or a small protected-key family before any further PPO. It should not run PPO
or change actor inputs.
