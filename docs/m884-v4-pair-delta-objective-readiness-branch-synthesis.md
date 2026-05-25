# M884 V4 Pair-Delta Objective-Readiness Branch Synthesis

## Purpose

M884 synthesizes the `v4_pair_delta_objective_readiness` branch before any
objective-only update, PPO, or promotion.

Covered milestones:

```text
M875-M883
```

M884 is synthesis-only:

```text
no replay
no actor update
no M761 residual-head update
no optimizer
no PPO
no checkpoint promotion
```

## Evidence Summary

M875 audited the raw M873 pair-delta corpus and rejected direct objective
design:

```text
new accepted rows: 39
unique closed-loop signatures: 13
duplication factor rows/signatures: 3.0
train_public new rows: 0
source_holdout new rows: 0
```

M876/M877 designed and implemented deduplication plus purpose-specific splits:

```text
dedup_rows: 247
new_dedup_rows: 13
new_duplicate_factor_after: 1.0
objective_train_rows: 124
objective_train_new_rows: 8
objective_eval_rows: 22
objective_eval_new_rows: 2
source_holdout_rows: 98
source_holdout_new_rows: 0
new_signature_holdout_rows: 3
```

M878 found that the deduped rows were cleaner but still not objective-ready
because they lacked concrete action target fields.

M879/M880 designed and implemented target-action enrichment:

```text
enriched dedup rows: 247
enriched train rows: 124
enriched eval rows: 22
enriched source holdout rows: 98
enriched new signature holdout rows: 3
identity_unique joins: 494 / 494
missing joins: 0
ambiguous joins: 0
target action fields present: true
```

M881 audited the enriched corpus and admitted design-only objective work, while
keeping actor update and PPO blocked.

M882 designed exact no-update objective sanity:

```text
pair_delta_improvement:
  prefer override_action over normal_action under the same normal observation
  and recurrent hidden state.

pair_delta_degradation:
  prefer normal_action over harmful override_action under the same normal
  observation and recurrent hidden state.
```

M883 implemented that exact sanity and passed:

```text
expected_rows: 247
tensor_rows_reconstructed: 247
missing_tensor_count: 0
snapshot_rows: 19
snapshot_rejections: 0
exact_losses_finite: true
improvement_rows_present: true
degradation_rows_present: true
objective_loss_mean: 1.7962036213105181
actor_parameters_changed: false
```

## Supported Claims

The branch supports these claims:

```text
M873 raw pair-delta evidence can be transformed into a cleaner objective-ready
corpus without duplicate axis pressure.

The transformed corpus now has new M873 evidence in train and eval, plus a
new-signature holdout.

Every dedup/split row can recover concrete normal, right, and override action
targets from sequence rows.

Every split row can be reconstructed into an actor observation and recurrent
hidden tensor for exact no-update objective evaluation.

The proposed improvement/degradation pair-delta preference objective is
computable and finite on the public corpus.
```

## Falsified Claims

The branch falsifies or weakens these claims:

```text
Raw M873 rows are objective-ready as-is.

Retarget-axis duplicate labels can be treated as independent objective samples.

Accepted-class labels alone are enough to design the objective.

Tensor reconstruction is the current blocker.

M883's exact objective sanity result is enough to justify PPO or promotion.
```

## Failure Taxonomy Summary

`objective_overfit`:

```text
Reduced by deduplication, train/eval/new-signature splits, and exact per-split
objective reporting. Still a risk for any future update because the corpus is
public and narrow.
```

`metric_artifact`:

```text
Reduced by exact identity joins and actor-state reconstruction. The main
remaining metric risk is treating the exact sanity loss as evidence that an
update will be beneficial.
```

`scenario_sampling_failure`:

```text
Still present. New source holdout is unavailable, eval/new-signature holdouts
contain only degradation rows, and 78055 remains absent from new accepted
pair-delta rows.
```

`contract_violation`:

```text
Not observed. Actor observation contract is unchanged and no hidden vehicle
parameters are introduced as actor inputs.
```

`lineage_invalid`:

```text
Reduced. Sequence source routing, source rows, scenario config, residual head,
checkpoint, and tensor reconstruction are explicit.
```

## Public Gate Overfit Risk

Public gate overfit risk is moderate to high:

```text
The corpus is now technically objective-ready, but it is still a public proof
surface built through many targeted transformations.
```

Controls required for the next branch:

```text
Start with a design-only objective-only probe milestone.
Run exact objective sanity before and after any update.
Use interpolation and full public gates before considering any checkpoint.
Do not tune coefficients against source_holdout or new_signature_holdout.
Do not run PPO until objective-only update behavior has been audited.
Do not claim source-generalization from this corpus.
```

## Next Branch Decision

Decision:

```text
promote_to_next_branch
```

Close current branch:

```text
v4_pair_delta_objective_readiness
```

Open new branch:

```text
v4_pair_delta_objective_probe
```

Next milestone:

```text
m885-v4-enriched-pair-delta-objective-only-probe-design
```

M885 may design a no-PPO objective-only probe, but must not run the probe. The
probe branch must keep checkpoint promotion blocked until exact objective,
replay, behavior, and branch-retention gates are audited.
