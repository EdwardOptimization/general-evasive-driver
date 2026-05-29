# M1525 Paper-Route T5 Response Mismatch Result Audit

## Summary

M1525 audits the M1524 response/action-history mismatch smoke.

Decision:

```text
t5_response_mismatch_audit_close_current_t5_wrong_history_route_to_branch_synthesis
```

M1524 is a clean diagnostic run and a strong negative result for the current T5
wrong-history route. Donor response/action mismatch strength was high, but donor
variants were near-null. Only the zero-current-response control remained
outcome-relevant. This means the current T5 subset is useful as a response
removal/timing-sensitivity probe, but not as a wrong-history or self-ID proof
surface.

The next step should be a short branch synthesis that closes this current T5
wrong-history route and pivots to fresh ambiguity/source mining, rather than
another narrow donor tweak.

## Audited Evidence

Audited run:

```text
runs/m1524_t5_response_mismatch_intervention_smoke
```

Summary:

```text
eligible_target_count: 4
anchor_count: 3
variant_count: 7
intervention_row_count: 84
target_replay_failure_count: 0
donor_replay_failure_count: 0
max_donor_response_l2_mean: 0.4977846671714798
max_margin_gap_from_normal: 0.021037607967195893
outcome_relevant_variant_count: 2
divergence_relevant_variant_count: 13
success_drop_count: 0
guardrail_violation_count: 0
```

Variant summary:

```text
donor_response_action_plus_hidden_from_anchor max_gap 0.000443
donor_response_action_stream_from_anchor      max_gap 0.000401
donor_ego_response_stream_from_anchor         max_gap 0.000410
donor_action_history_stream_from_anchor       max_gap 0.000008
donor_response_current_frame_at_anchor        max_gap 0.000029
zero_current_response_from_anchor             max_gap 0.021038
```

Anchor summary:

```text
decision          max_gap 0.010080  outcome_relevant 0
decision_minus_8  max_gap 0.021038  outcome_relevant 1
reveal            max_gap 0.021038  outcome_relevant 1
```

## Interpretation

The donor mismatch was not weak:

```text
max donor_response_l2_mean: 0.4977846671714798
mean donor_response_l2 for donor variants: about 0.265
```

Despite that, donor response/action variants barely changed terminal margin.
This makes the result more informative than a null result with weak donors.

Supported claims:

```text
response-mismatch harness works and records donor mismatch strength;
zeroing current response still reduces margin in the strongest low-mu timing
rows;
the current T5 subset is dominated by target scene/current dynamics enough that
donor response/action mismatch does not induce wrong behavior.
```

Unsupported claims:

```text
wrong-history causal dependence;
history-necessity proof;
candidate materialization;
training corpus export;
level3 anticipatory self-identification.
```

## Failure Taxonomy

Failure labels:

```text
scenario_sampling_failure
metric_artifact
```

`scenario_sampling_failure` applies because the current T5 rows do not create a
decision boundary where donor response/action mismatch changes behavior.

`metric_artifact` applies because zero-current control positives could be
over-claimed as self-ID if not separated from wrong-history variants.

No contract violation, private holdout contamination, training instability,
promotion misuse, or PPO washout occurred.

## Decision

Close the current T5 wrong-history route as insufficient.

Do not materialize candidates.

Do not export a training corpus.

Do not run PPO or train from these rows.

Route to branch synthesis:

```text
m1526-paper-route-t5-timing-amplified-branch-synthesis
```

The synthesis should preserve M1521/M1524 as useful negative and diagnostic
evidence, then pivot to a fresh ambiguity/source-mining route. The new route
should search for scenarios where hidden dynamics or response history change the
preferred action under similar current scene context, rather than continuing to
massage the same four T5 rows.

## Next-Route Recommendation

The next branch should focus on fresh source mining for:

```text
matched current scene/context;
larger hidden-dynamics action divergence;
near-boundary terminal margins;
strong donor response mismatch;
wrong-history or response-mismatch gap before boundary retargeting;
source diversity beyond the current four T5 rows.
```

Do not use private holdout. Do not train. Start with metadata/source mining and
bounded public probes.

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
m1526-paper-route-t5-timing-amplified-branch-synthesis
```
