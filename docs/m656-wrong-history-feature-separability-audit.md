# M656 Wrong-History Feature Separability Audit

## Purpose

M656 audits the M655 no-training feature separability result and chooses the
next branch.

This milestone is audit-only:

```text
no training
no PPO
no actor update
no checkpoint promotion
```

## M655 Result

M655 classified the M652 blocker as:

```text
fusion_washout
```

The run was contract-clean:

```text
actor_parameters_changed: false
checkpoint_written: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
```

## Key Metrics

| Variant | Raw Hidden L2 | Next Hidden L2 | Fused Feature L2 | Actor Action L2 |
| --- | ---: | ---: | ---: | ---: |
| delayed_history | 0.556773 | 0.182988 | 0.073534 | 0.013368 |
| wrong_matched_history | 0.097340 | 0.039664 | 0.014905 | 0.000685 |

Retention ratios:

| Variant | Next / Raw | Feature / Raw | Action / Feature |
| --- | ---: | ---: | ---: |
| delayed_history | 0.327317 | 0.132473 | 0.184880 |
| wrong_matched_history | 0.409547 | 0.154235 | 0.045922 |

Wrong-history is much weaker than delayed-history at the deployed boundary:

```text
wrong_to_delayed_feature_l2_ratio: 0.202695
wrong_to_delayed_action_l2_ratio: 0.051232
```

## Source Split Check

The two wrong-history sources agree:

| Source | Split | Rows | Raw Hidden L2 | Fused Feature L2 | Actor Action L2 |
| ---: | --- | ---: | ---: | ---: | ---: |
| 30 | train | 39 | 0.089258 | 0.014962 | 0.000792 |
| 32 | source_holdout_validation | 64 | 0.105421 | 0.014848 | 0.000578 |

This is not a single-source artifact. The source-heldout wrong-history branch
is slightly weaker at the action boundary.

## Rejected Explanations

M656 rejects:

```text
the stored wrong-history intervention is absent:
  raw_hidden_l2 = 0.097340

the GRU update fully erases history:
  next_hidden_retention_ratio = 0.409547

the M655 runner accidentally trained or changed the actor:
  checksum unchanged and no checkpoint written

M652 failed only because contrast_coef was too small:
  the feature/action boundary itself gives the head a very small gap
```

## Current Interpretation

The strongest reading is:

```text
wrong-history information exists in recurrent state,
survives the current-response GRU update,
but is weak at the fused response/context feature boundary
and even weaker after the actor action head.
```

This explains the recent sequence:

```text
M649:
  normal sequence-delta head learnable

M652:
  wrong-history contrast does not create useful gap

M655:
  wrong-history fused-feature/action gap is tiny relative to delayed-history
```

So the immediate blocker is not PPO, not a missing normal BC target, and not a
need to increase the frozen-head contrast coefficient. The blocker is that the
feature view used by the auxiliary head may be the wrong diagnostic boundary.

## Next Branch

M657 should design a frozen feature-view comparison probe:

```text
view A: fused actor feature      (current M649-M652 boundary)
view B: next recurrent hidden    (pre-fusion belief state)
view C: fused feature + next hidden
```

For each view, train only a diagnostic auxiliary sequence-delta head with the
same normal-target and wrong-history contrast style as M652. The actor remains
frozen and no checkpoint is promoted.

The probe should answer:

```text
Does wrong-history separation become learnable when the head sees next_hidden
instead of only fused actor features?
```

If yes, the next true design target is the response/context fusion boundary.
If no, the next target is stronger wrong-history corpus mining or a different
objective, not actor coupling.

## Forbidden Next Steps

Do not:

- run PPO;
- update the actor;
- promote a checkpoint;
- tune M652 contrast coefficients on fused features only;
- claim closed-loop self-ID proof from M655 distances.

## Decision

`wrong_history_feature_separability_audit_admit_fusion_boundary_probe_design`

## Next

`m657-wrong-history-fusion-boundary-probe-design`
