# M1526 Paper-Route T5 Timing-Amplified Branch Synthesis

## Summary

M1526 synthesizes the M1521-M1525 T5 timing-amplified branch.

Decision:

```text
t5_timing_amplified_synthesis_close_current_t5_route_promote_fresh_ambiguity_mining
```

Synthesis decision:

```text
promote_to_next_branch
```

The branch produced a useful positive control and a useful negative result:

```text
M1521: earlier reset/zero-current interventions can reduce terminal margin.
M1524/M1525: high-strength donor response/action mismatch remains near-null.
```

Therefore the current four-row T5 route is closed as a wrong-history/self-ID
proof route. The next branch should mine fresh ambiguous sources where hidden
dynamics or response history actually change the preferred action under similar
scene context.

No candidate materialization, corpus export, training, PPO, promotion, private
holdout, actor-input change, or level3 self-identification claim is admitted.

## Evidence Summary

### M1521 Timing-Amplified Positive Control

M1521 implemented earlier-window interventions:

```text
eligible_target_count: 4
anchor_count: 4
variant_count: 7
intervention_row_count: 112
target/donor replay failure count: 0/0
max_margin_gap_from_normal: 0.027952724375794435
outcome_relevant_variant_count: 9
success_drop_count: 0
guardrail_violation_count: 0
```

Positive signal:

```text
reset_hidden_every_step_from_anchor and zero_current_response_from_anchor
reduced terminal margin when started from reveal or decision_minus_8.
```

Interpretation:

```text
decision-step intervention was too late;
the harness can expose timing-sensitive response removal effects;
the result is not wrong-history self-identification.
```

### M1522 Audit

M1522 correctly separated:

```text
timing sensitivity: supported;
wrong-history evidence: not supported;
candidate materialization: blocked.
```

It routed to response/action-history mismatch design.

### M1524 Response Mismatch Negative Result

M1524 implemented donor response/action mismatch:

```text
eligible_target_count: 4
anchor_count: 3
variant_count: 7
intervention_row_count: 84
target/donor replay failure count: 0/0
max_donor_response_l2_mean: 0.4977846671714798
max_margin_gap_from_normal: 0.021037607967195893
outcome_relevant_variant_count: 2
success_drop_count: 0
```

Variant result:

```text
donor response/action variants max gap: <= 0.000443
zero_current_response_from_anchor max gap: 0.021038
```

Interpretation:

```text
donor mismatch was strong by input distance;
donor response/action mismatch still did not produce meaningful behavior change;
zero-current response remained the only positive control.
```

### M1525 Audit

M1525 closed the current T5 wrong-history route:

```text
current_t5_wrong_history_route_verdict: close_as_insufficient
candidate_materialization_verdict: blocked
training_corpus_export_verdict: blocked
```

## Supported Claims

Supported:

```text
bounded timing intervention infrastructure works;
moving intervention earlier exposes margin sensitivity that decision-step
intervention missed;
zeroing current response can reduce margin on the strongest T5 low-mu rows;
response/action mismatch harness preserves target scene context and measures
donor mismatch strength;
the current T5 donor-hidden and donor-response mismatch route is not a strong
wrong-history proof route.
```

## Falsified Or Unsupported Claims

Falsified for this current T5 route:

```text
hidden-only donor wrong-history produces outcome-relevant behavior changes;
donor response/action stream mismatch produces outcome-relevant behavior changes;
the four current T5 high-speed rows are sufficient for wrong-history proof.
```

Unsupported:

```text
success-drop evidence;
candidate materialization;
training corpus export;
level3 anticipatory self-identification;
policy superiority.
```

## Failure Taxonomy Summary

Failure labels:

```text
scenario_sampling_failure
metric_artifact
```

`scenario_sampling_failure`:

```text
The current T5 rows remain too scene/current-response dominated to expose
wrong-history dependence, even with high donor response mismatch strength.
```

`metric_artifact`:

```text
Zero-current positives are easy to over-claim. They prove response removal can
matter, not that the policy uses history for online self-identification.
```

No contract violation, private holdout contamination, PPO washout, promotion
misuse, or training instability occurred.

## Public-Gate Overfit Risk

Risk:

```text
high
```

Reasons:

```text
all M1521-M1525 evidence uses the same four public T5 rows;
multiple intervention designs were shaped by those rows;
the strongest positive signal comes from controls rather than wrong-history
variants;
no private holdout was used.
```

This risk is acceptable for probe development, but it blocks paper-level claims
or materialization from this subset.

## Next Branch Decision

Promote to a new branch:

```text
paper_route_fresh_ambiguity_source_mining
```

Next milestone:

```text
m1527-paper-route-fresh-ambiguity-source-mining-design
```

The new branch should search for scenarios with:

```text
matched current scene/context;
similar current ego state;
hidden dynamics or response history that imply different preferred actions;
near-boundary margins;
source diversity beyond the current four T5 rows;
explicit donor mismatch strength;
wrong-history or response-mismatch gap before any training corpus export.
```

The first milestone should be design only. It should not train, run PPO,
materialize candidates, use private holdout, or claim self-identification.

## Guardrails

```text
candidate_materialized: false
training_started: false
evaluation_started: false
replay_started: false
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
m1527-paper-route-fresh-ambiguity-source-mining-design
```
