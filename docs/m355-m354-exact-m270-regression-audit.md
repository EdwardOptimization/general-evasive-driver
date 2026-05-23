# M355 M354 Exact M270 Regression Audit

M355 audits why M354 failed exact M270 after the fresh-seed short PPO repeat.
It does not promote a checkpoint and does not run PPO or downstream replay
gates.

## Question

M354 rejected this candidate:

```text
runs/m354_exact_repair_from_raw_s40_seed10103/candidate_checkpoint.pt
```

The exact repair improved M297 but regressed M270:

| Objective | Delta vs M352 | Pass |
| --- | ---: | --- |
| Exact M297 rejected-history preference | -0.000023007 | true |
| Exact M270 source-balanced outcome | +0.000040591 | false |

The audit question is whether this means the raw PPO proposal is intrinsically
unrepairable, or whether the exact repair endpoint selection is too coarse.

## Trace Finding

The repair loop records `train_metrics.csv` before each optimizer update is
applied. In `exact_post_ppo_repair.py`, the loss terms are computed, gradients
are applied with `optimizer.step()`, and then the previously computed terms are
written into the metrics list.

Therefore the original M354 `step=40` row is the state before the 40th Adam
update, not the final saved checkpoint after that update.

Original M354 trace:

| State | Exact M297 | Exact M270 | M297 delta | M270 delta | Pass |
| --- | ---: | ---: | ---: | ---: | --- |
| Base M352 | 1.189182401 | 0.677673042 | 0.000000000 | 0.000000000 | true |
| Raw PPO | 1.190529585 | 0.678606987 | +0.001347184 | +0.000933945 | false |
| Step 39 / pre-step-40 | 1.189003229 | 0.677619696 | -0.000179172 | -0.000053346 | true |
| Final step 40 checkpoint | 1.189159393 | 0.677713633 | -0.000023007 | +0.000040591 | false |

## Diagnostic Rerun

M355 reran the same exact repair command with `--steps 39`:

```text
runs/m355_m354_repair_step39_diagnostic
```

The 39-step diagnostic candidate exactly matches the original M354 pre-step-40
metrics:

| Metric | Value |
| --- | ---: |
| Exact M297 | 1.189003229 |
| Exact M270 | 0.677619696 |
| Exact M297 delta vs M352 | -0.000179172 |
| Exact M270 delta vs M352 | -0.000053346 |
| Exact lexicographic pass | true |

This proves the M354 PPO proposal had a lexicographically feasible repaired
state during exact repair. The rejected endpoint failed because the tool saved
the last optimizer state, not the best exact-feasible state.

## Classification

Failure classification:

```text
metric_artifact
```

The original M354 `objective_overfit` classification remains valid for the
saved endpoint, but M355 refines the root cause: the tool's logged metrics did
not describe the saved state, and the candidate-selection policy discarded a
better intermediate state.

## Decision

Do not retry PPO yet. Do not promote the 39-step diagnostic candidate, because
it has not passed source-diverse, old-key neighborhood, first replay, or full
public gates.

Admit M356:

```text
m356-exact-repair-best-step-selection-implementation
```

M356 should update the exact repair tool so that it evaluates post-update exact
metrics and can save the best lexicographically feasible checkpoint instead of
blindly saving the final optimizer step. After that implementation, a later
milestone can rerun the M354 repair using the corrected selection policy.
