# M1462 Paper-Route Retargeted Bounded Replay Result Audit

## Summary

M1462 audits the M1461 retargeted source-step bounded replay result.

Decision:

```text
retargeted_bounded_replay_positive_singleton_route_to_neighborhood_expansion_design
```

Failure type:

```text
scenario_sampling_failure
```

M1462 does not run replay, train, run PPO, promote, use private holdout, export
corpus, or change actor inputs.

## Audit Finding

M1461 is a meaningful branch improvement:

```text
M1452 history_positive_rows: 0
M1461 history_positive_rows: 2
```

The positive rows are real bounded-replay rows, not preflight rows. They are
normal-viable, action-critical, outcome-critical, and history-positive under
the existing public smoke criterion.

However, the result is not source-diverse enough:

```text
history_positive_rows: 2
history_positive_unique_source_seeds: 1
history_positive_unique_capability_pairs: 1
history_positive_unique_reveal_buckets: 1
history_positive_unique_variants: 1
```

The same source also produces strong zero-current control sensitivity:

```text
control_positive_rows: 8
control_positive_unique_source_seeds: 1
control_positive_unique_capability_pairs: 1
```

So the supported claim is narrow:

```text
boundary retargeting found a live outcome-sensitive neighborhood.
```

The unsupported claim remains:

```text
we have a source-diverse history-necessity corpus ready for training.
```

## Interpretation

M1461 should not be discarded. It is the first evidence that the boundary
retargeting branch can create actual history-positive replay rows.

It should also not be overclaimed. With only a singleton positive source, using
it as a training corpus would risk optimizing a fixed public row and repeating
the earlier proof-row overfitting pattern.

## Next Design Requirement

M1463 should design a positive-neighborhood expansion that:

```text
keeps M1461's live positive source as an anchor;
searches nearby relocations around the positive boundary;
adds source-diverse neighboring seeds / capability pairs when possible;
separates history-positive rows from zero-current control positives;
does not train, export corpus, promote, or change actor inputs.
```

The next replay surface should target:

```text
history_positive_rows > 2
history_positive_unique_source_seeds >= 2 if available
history_positive_unique_capability_pairs >= 2 if available
control-positive rows reported separately
normal_failed_rows reduced relative to broad failed-source sampling
```

## Guardrails

M1462 guardrail status:

```text
replay_started: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
training_corpus_exported: false
actor_input_contract_changed: false
level3_self_id_claim_made: false
```

## Next Route

Admit:

```text
m1463-paper-route-positive-neighborhood-expansion-design
```
