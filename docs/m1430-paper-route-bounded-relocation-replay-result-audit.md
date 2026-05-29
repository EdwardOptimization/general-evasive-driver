# M1430 Paper-Route Bounded Relocation Replay Result Audit

## Summary

M1430 audits the M1429 replay smoke before any replay retuning or training.

Decision:

```text
bounded_relocation_replay_audit_admit_geometry_aware_selector_design
```

M1430 does not run replay, train, run PPO, promote, use private holdout, export
a training corpus, or change actor inputs.

## What M1429 Proved

M1429 proved that the bounded relocation replay tool is live:

```text
selected_candidate_rows: 128
actual_replay_rows: 384
rejected_rows: 0
actor_parameters_changed: false
actor_input_contract_changed: false
```

It also proved the accounting path is clean:

```text
history_positive_rows: 0
control_positive_rows: 0
reset_hidden rows: 128
zero_current_response rows: 128
warmup_removed rows: 128
```

Controls were reported separately and were not mixed into history-positive
counts.

## What M1429 Did Not Prove

M1429 does not prove that history is unnecessary. The selected rows were not a
valid forward-obstacle source set:

```text
selected_unique_source_seeds: 3
selected_unique_variants: 1
selected_max_single_seed_share: 0.75
normal_failed_rows: 177 / 384
normal_success selected groups: 69 / 128
source_body_x median: -1.678050
relocated_body_x clipped to 2.0m: 126 / 128 selected groups
```

Most source snapshots had the obstacle behind the vehicle. The replay tool
clipped those to the minimum forward body distance, creating a geometry-poor
test. That makes M1429 a valid implementation exercise but not strong
scientific evidence about history necessity.

## Failure Classification

Classification:

```text
scenario_sampling_failure
geometry_selector_failure
```

The primary problem is source selection:

```text
candidate ranking preferred high action divergence;
it did not preflight source obstacle geometry;
it let one seed dominate;
it selected only warmup_removed;
it replayed mostly clipped near-body obstacle placements.
```

## Blocked Interpretations

Do not claim:

```text
actual relocated replay disproves history usefulness;
M1425/M1429 rows are ready for training;
the threshold should be lowered after the result;
another larger replay sweep with the same selector is justified.
```

## Next Route

Admit a design-only milestone:

```text
m1431-paper-route-geometry-aware-replay-selector-design
```

The next design should add a geometry preflight stage before replay:

```text
1. reconstruct traces for candidate rows without running full replay;
2. compute source_body_x, source_body_y, source_half_width;
3. reject rows whose source obstacle is behind or too close;
4. reject rows whose relocation would be clipped to min_body_x;
5. cap per seed, capability pair, reveal bucket, and variant;
6. prefer multiple history variants, not only warmup_removed;
7. only then admit a bounded replay run.
```

Candidate public gates for that future preflight:

```text
forward_geometry_rows >= 64
unique_source_seeds >= 6
unique_capability_pairs >= 8
unique_reveal_buckets >= 6
unique_history_variants >= 2
max_single_seed_share <= 0.35
relocation_clipped_share <= 0.10
```

If those gates cannot be met from M1425 rows, the branch should synthesize or
return to source mining instead of retuning replay thresholds.

## Guardrails

M1430 guardrail status:

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

## Conclusion

M1429 is a useful negative, but it is a negative about the selector, not about
the underlying self-ID hypothesis. The next highest-leverage step is a
geometry-aware replay selector design with source-diversity and unclipped
forward-obstacle gates.
