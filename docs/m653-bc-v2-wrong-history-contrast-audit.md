# M653 BC-v2 Wrong-History Contrast Audit

## Purpose

M653 audits the failed M652 frozen-head wrong-history contrast smoke. It
separates the normal-retention success from the wrong-history gap failure and
decides the next blocker.

This milestone is audit-only:

```text
no training
no PPO
no actor update
no checkpoint promotion
```

## M652 Classification

M652 is classified as:

```text
normal_retention_positive_wrong_history_gap_negative
```

The contrast implementation ran cleanly:

```text
passed_seed_count: 0 / 3
contrast_passed: false
actor_parameters_changed: false
all_best_heads_written: true
actor_checkpoint_written: false
```

## What Worked

Normal sequence-delta learning was preserved:

| Seed | Normal Validation MSE | Threshold |
| ---: | ---: | ---: |
| 6510 | 0.000491 | <= 0.0010 |
| 6511 | 0.000508 | <= 0.0010 |
| 6512 | 0.000509 | <= 0.0010 |

This confirms that adding the contrast terms did not destroy ordinary local
correction learning.

## What Failed

Wrong-history separation did not move meaningfully:

| Seed | Train Gap MSE | Val Gap MSE | Train Gap L2 | Val Gap L2 |
| ---: | ---: | ---: | ---: | ---: |
| 6510 | 0.000004 | -0.000003 | 0.000940 | 0.000748 |
| 6511 | 0.000003 | -0.000002 | 0.000700 | 0.000624 |
| 6512 | 0.000005 | -0.000003 | 0.000774 | 0.000729 |

The target thresholds were:

```text
wrong_train_gap_mse >= 0.00025
wrong_validation_gap_mse >= 0.00010
wrong_train_prediction_gap_l2 >= 0.01
wrong_validation_prediction_gap_l2 >= 0.005
```

The observed gaps are one to two orders of magnitude too small, and validation
gap MSE is negative for every seed. This is not close to passing.

## Likely Cause

The most likely blocker is frozen-feature separability:

```text
BC5660's frozen recurrent feature representation may not expose enough
normal-vs-wrong-history difference on sources 30 and 32 for a small head to
separate them.
```

This is more plausible than "contrast coefficient too small" because:

- normal target learning remains strong;
- the wrong-history prediction L2 gap remains below `0.001`;
- train and source-heldout wrong-history gaps both fail;
- the failure is consistent across all three seeds.

Increasing contrast coefficients before checking feature distances would be
poor process. It could produce unstable head behavior without proving that the
features contain usable self-ID information.

## Rejected Next Steps

Do not:

- couple the head into the actor;
- increase contrast coefficients immediately;
- run PPO from this branch;
- claim self-ID evidence from normal validation retention.

## Next Branch

M654 should design a wrong-history feature separability audit.

It should measure, at minimum:

```text
feature_l2(normal, wrong)
feature_cosine(normal, wrong)
hidden_l2(normal_hidden, wrong_hidden)
head_jacobian_sensitivity if cheap
normal-vs-wrong separability by source and split
comparison against delayed-history rows
```

The audit should answer:

```text
Is the wrong-history information present in frozen BC5660 features but not used
by the current head objective, or is it absent/too small in the frozen features?
```

## Decision

`bc_v2_wrong_history_contrast_audit_admit_feature_separability_design`

## Next

`m654-wrong-history-feature-separability-audit-design`
