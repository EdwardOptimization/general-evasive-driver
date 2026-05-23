# M303 M302 Preference-Guard Failure Audit

M303 audits why the M302 rejected-history preference PPO guard failed. No PPO
was run, no actor update was run, and actor inputs are unchanged.

## Failure Recap

M302 added a sampled training-time auxiliary loss:

```text
rejected_history_preference_aux_coef = 0.03
```

The PPO training metric reported:

```text
rejected_history_preference_loss_mean = 1.1774653842051823
```

But exact post-PPO evaluation regressed:

| Objective | M299 base | M302 raw | Delta |
| --- | ---: | ---: | ---: |
| Exact M297 rejected preference | 1.189609528 | 1.190309286 | +0.000699759 |
| Exact M270 | 0.677945912 | 0.678388774 | +0.000442863 |

Every nonzero interpolation alpha also regressed both exact objectives.

## Row-Level Diagnosis

The M297 regression is broad, not a single-row artifact.

```text
17 / 17 rows have higher combined loss at M302 raw.
```

Largest combined-loss increases:

| Row | Delta | Weight |
| ---: | ---: | ---: |
| 2 | +0.001437 | 0.024055 |
| 3 | +0.001434 | 0.024612 |
| 0 | +0.001160 | 0.024373 |
| 1 | +0.001157 | 0.024926 |
| 4 | +0.001041 | 0.022766 |
| 5 | +0.001037 | 0.023282 |
| 6 | +0.000903 | 0.327499 |
| 7 | +0.000901 | 0.020932 |
| 11 | +0.000832 | 0.056911 |
| 8 | +0.000808 | 0.018425 |

Focused rows 6, 11, 15, and 16 all worsen monotonically with alpha.

## Sampled Metric Mismatch

The train-time metric is sampled during the PPO update. It is not a full-corpus
exact gate, and in M302 it was misleading:

```text
sampled train metric = 1.177465
exact base loss      = 1.189610
exact raw loss       = 1.190309
```

The sampled metric can look acceptable because it samples rows with replacement
inside the update and reports the loss value observed during training, not the
deterministic exact loss of the final checkpoint.

This is a metric-artifact problem for promotion. The metric is still useful for
debugging whether the loss is wired, but it cannot replace the exact M297 gate.

## Interpretation

M302 did not fail because one protected row is stale. It failed because the PPO
update direction is globally misaligned with both exact M297 and exact M270, and
the scalar auxiliary coefficient did not make the exact objectives lexicographic.

Increasing the coefficient might reduce this failure, but that would be another
PPO tuning attempt without a stronger guarantee. The better next step is to
make exact full-corpus objectives first-class in a post-PPO repair/projection
step.

## Recommended Repair

Design an exact lexicographic post-PPO repair:

```text
1. Start from M302 raw only as a rejected candidate.
2. Optimize full-batch exact M297 preference and exact M270 loss.
3. Add a trust-region or action-anchor term to M299 to avoid replay collapse.
4. Accept only candidates that do not regress exact M297 or exact M270.
5. Then run M183/M170 and M267/M264 first replay gates.
6. Only after that run full replay, protected-key, and behavior gates.
```

This keeps PPO exploration separate from promotion: PPO can propose a candidate,
but exact objectives decide whether any repaired/projection checkpoint deserves
closed-loop replay evaluation.

## Decision

Repair path:

```text
repair_with_exact_lexicographic_post_ppo_projection
```

Failure types:

```text
metric_artifact
objective_overfit
```

Next step:

```text
m304-exact-lexicographic-post-ppo-repair-design
```
