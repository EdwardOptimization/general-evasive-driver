# M1558 Paper-Route Calibrated Pair-Expansion Branch Synthesis After Active-Set Miner

## Summary

M1558 synthesizes the calibrated pair-expansion branch after M1550-M1557.

Synthesis decision:

```text
promote_to_next_branch
```

Decision:

```text
calibrated_pair_expansion_synthesis_promote_to_recoverable_active_set_generation_branch
```

The calibrated pair-expansion branch repaired the pair-count bottleneck, but it
did not produce terminal-boundary history-sensitivity evidence. The remaining
blocker is not matched-pair quantity. It is recoverable active-set generation:
the branch failed to produce source-diverse anchors where bounded local control
can still affect terminal boundary outcome.

The next branch is:

```text
paper_route_recoverable_active_set_generation
```

## Evidence Summary

M1549 designed pairability-first calibrated source expansion.

M1550 implemented it and produced:

```text
accepted_pair_count: 21
accepted_source_family_edge_count: 5
max_single_pair_source_edge_share: 0.38095238095238093
accepted_terminal_family_count: 4
accepted_window_bucket_count: 3
passes_public_smoke_gates: false
```

M1551 audited that result as pair-gate pass with a snapshot-count caveat.

M1552 designed pair-expanded calibrated history interventions.

M1553 implemented the pair-expanded intervention smoke:

```text
intervention_row_count: 420
anchor_replay_failure_count: 0
passes_public_smoke_gates: true
passes_evidence_quality_targets: false
terminal_max_history_margin_gap: 0.00025038157254009263
terminal_wrong_history_positive_target_sides: 0
terminal_donor_plus_hidden_positive_target_sides: 0
terminal_wrong_or_donor_success_drop_count: 0
```

M1554 audited this as a clean public-pass but history-null result.

M1555 designed the temporal active-set miner to test whether earlier temporal
windows over those sources were locally controllable before another history
intervention.

M1556 implemented the miner:

```text
anchor_candidate_count: 96
local_perturbation_row_count: 576
action_sensitive_anchor_count: 2
active_source_family_count: 1
active_anchor_window_count: 1
success_flip_count: 4
collision_flip_count: 0
max_abs_terminal_margin_gap: 0.010894415363880583
passes_public_smoke_gates: false
passes_evidence_quality_targets: false
```

M1557 audited the result as clean implementation but sparse active-set failure.
The near-boundary rows were all collision outcomes, and one-step local
perturbations did not recover them.

## Supported Claims

The branch supports these claims:

```text
calibrated pair-expansion can produce a larger source-diverse pair set than M1547;
pair-expanded intervention replay is deterministic and clean at the plumbing level;
direct history intervention over M1550 pairs is null under the tested anchors;
temporal local-action-sensitivity mining can be implemented without training or actor-input changes;
current calibrated sources do not provide source-diverse recoverable active-set anchors.
```

## Unsupported Claims

The branch does not support:

```text
terminal-boundary history necessity;
wrong-history success-drop evidence on T5 terminal rows;
candidate materialization;
training corpus export;
PPO continuation;
checkpoint promotion;
paper-level self-identification evidence;
level3 anticipatory self-identification.
```

## Falsified Claims

The branch falsifies two narrower working hypotheses:

```text
1. Pair count alone was the reason calibrated terminal-boundary intervention was null.
2. Earlier temporal windows over the same calibrated pair-expansion sources are enough to create a usable active set.
```

Both are now false under current public evidence.

## Failure Taxonomy Summary

```text
scenario_sampling_failure
metric_artifact
```

`scenario_sampling_failure` is the primary current blocker: the branch did not
generate recoverable source-diverse active-set anchors.

`metric_artifact` was local to M1556 implementation: failed-anchor NaN rows could
be counted as active before correction. The final M1556 result uses the
corrected counting.

## Public-Gate Overfit Risk

Public-gate overfit risk is high.

The branch has repeatedly optimized around public calibrated rows:

```text
M1550 pair-expanded source rows;
M1553 pair-expanded intervention anchors;
M1556 temporal windows over the same source family pool.
```

Another implementation over this same source construction would likely become a
gate-passing exercise. The next useful evidence step must change the source
generation objective, not merely add another intervention variant.

## Next Branch Decision

Promote to a new branch:

```text
paper_route_recoverable_active_set_generation
```

The new branch should target:

```text
recoverable terminal-boundary active-set rows;
source-diverse anchors where local control can change terminal outcome;
multi-step local action holds as a controllability diagnostic;
explicit triage of already-colliding, high-margin-safe, and recoverable-boundary anchors;
no history intervention replay until active-set gates pass;
no materialization, training, PPO, private holdout, actor-input change, corpus export, or level3 self-ID claim.
```

The first milestone should be a design-only step:

```text
m1559-paper-route-recoverable-active-set-generation-design
```

## Guardrails

```text
history_interventions_executed: false
candidate_materialized: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
training_corpus_exported: false
labels_enter_actor_input: false
level3_self_id_claim_made: false
```

## Next

```text
m1559-paper-route-recoverable-active-set-generation-design
```
