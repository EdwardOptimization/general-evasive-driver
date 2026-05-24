# M650 BC-v2 Head-Only Repeat Audit

## Purpose

M650 audits the M649 multi-seed frozen-head repeat before any adapter or
actor-coupling design. It separates the positive learnability evidence from the
negative wrong-history separation evidence.

This milestone is audit-only:

```text
no training
no PPO
no actor update
no checkpoint promotion
```

## Positive Evidence

M649 passed the pre-registered repeat gate:

```text
passed_seed_count: 3 / 3
repeat_passed: true
all_actor_checksums_unchanged: true
all_best_heads_written: true
all_final_heads_written: true
actor_checkpoint_written: false
```

Seed-level best-validation results:

| Seed | Best Epoch | Best Validation MSE | Validation Improvement | Final / Best Val | Passed |
| ---: | ---: | ---: | ---: | ---: | --- |
| 6460 | 52 | 0.000486 | 0.943446 | 1.604452 | true |
| 6461 | 39 | 0.000458 | 0.961764 | 1.193386 | true |
| 6462 | 47 | 0.000502 | 0.930663 | 2.276952 | true |

This establishes:

```text
the M641 local sequence-delta targets are repeatedly learnable from frozen
BC5660 features under source-balanced weighting.
```

It also fixes the M646 final-epoch overfit issue at the head-selection level by
saving best-validation heads.

## Negative Evidence

Wrong-history source separation remains essentially absent:

| Seed | Source | Target | Normal MSE | Variant MSE | Gap L2 |
| ---: | ---: | --- | ---: | ---: | ---: |
| 6460 | 30 | braking | 0.000330 | 0.000330 | 0.000648 |
| 6460 | 32 | yaw | 0.000441 | 0.000440 | 0.000596 |
| 6461 | 30 | braking | 0.000319 | 0.000317 | 0.000704 |
| 6461 | 32 | yaw | 0.000429 | 0.000430 | 0.000598 |
| 6462 | 30 | braking | 0.000328 | 0.000330 | 0.000651 |
| 6462 | 32 | yaw | 0.000462 | 0.000461 | 0.000526 |

This means the frozen head learns a nearly history-invariant correction on
wrong-history rows. It does not learn:

```text
normal history should predict the corrective sequence;
wrong history should not predict the same corrective sequence.
```

That is exactly the self-ID distinction the project cares about.

## Classification

M650 classifies M649 as:

```text
pass_with_wrong_history_limitation
```

The head-only branch is now strong enough to say the sequence-delta targets are
learnable from frozen features. It is not strong enough to justify actor
coupling, because coupling this head into the actor would likely inject a
generic correction rather than a history-conditioned correction.

## Rejected Next Step

Do not proceed directly to adapter or actor-coupling design.

Reason:

```text
the exact branch evidence says the auxiliary head does not separate normal and
wrong recurrent histories on sources 30 and 32.
```

Actor coupling should require a self-ID gate, not only a low source-balanced
sequence loss.

## Next Branch

M651 should design a wrong-history contrast objective for the head-only branch.

Minimum objective:

```text
normal prediction should approach delta_star
wrong-history prediction should not approach the same delta_star
```

Candidate terms:

```text
L_normal_target =
  masked_mse(head(o, h_normal), delta_star)

L_wrong_rejection =
  softplus(margin + d_normal - d_wrong)

where:
  d_normal = masked_mse(head(o, h_normal), delta_star)
  d_wrong  = masked_mse(head(o, h_wrong), delta_star)
```

Optional anchor:

```text
L_wrong_zero_delta_anchor =
  masked_mse(head(o, h_wrong), 0)
```

The anchor should be designed carefully because not all variant histories are
necessarily wrong-history histories. M651 should distinguish:

```text
wrong_matched_history rows: contrast required
delayed_history rows: diagnostic/reporting first
```

## Decision

`bc_v2_head_only_repeat_audit_pass_with_wrong_history_limitation_admit_contrast_design`

## Next

`m651-bc-v2-wrong-history-contrast-design`
