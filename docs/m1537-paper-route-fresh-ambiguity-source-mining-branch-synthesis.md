# M1537 Paper-Route Fresh Ambiguity Source-Mining Branch Synthesis

## Summary

M1537 synthesizes the M1527-M1536 fresh ambiguity/source-mining branch before any
further implementation milestone.

Decision:

```text
fresh_ambiguity_source_mining_synthesis_continue_to_source_expanded_repeat
```

Synthesis decision:

```text
continue
```

The branch has produced a real improvement over the earlier closed T5 route:
source-diverse public planning works, measured pair mining works, history
intervention plumbing works, and M1534 produced preliminary wrong-history and
donor-response/action-plus-hidden positives. The evidence is still source-small,
T4-only, control-sensitive, and public. Therefore the branch should continue
only to the source-expanded repeat implementation designed by M1536.

No candidate materialization, corpus export, training, PPO, promotion, private
holdout, actor-input change, or level3 self-identification claim is admitted.

## Evidence Summary

### M1527-M1529 Source Planning

M1527 pivoted from the closed four-row T5 route into fresh ambiguity mining:

```text
target: matched scene/current-state rows where hidden dynamics or older
        response history imply different preferred actions
guardrail: no materialization, no training, no self-ID claim
```

M1528 implemented the dry planner:

```text
source_row_count: 112
source_family_count: 14
proxy_fault_family_count: 7
closed_t5_subset_share: 0.0
guardrail_violation_count: 0
```

M1529 audited this as source-diverse and guardrail-clean enough to admit
measured public source mining.

### M1530-M1532 Measured Mining

M1530 designed fixed-policy measured mining with scene/current-state pairing,
recent/older evidence metrics, and no-materialization guardrails.

M1531 implemented and ran the bounded measured smoke:

```text
trace_row_count: 1226
measured_pair_candidate_count: 10
accepted_measured_pair_count: 3
target_replay_failure_count: 1
donor_replay_failure_count: 0
history_interventions_executed: false
passes_public_smoke_gates: true
passes_evidence_quality_targets: false
guardrail_violation_count: 0
```

M1532 correctly audited this as clean measured-pair plumbing, not self-ID
evidence, and admitted only a history-intervention design.

### M1533-M1535 History Interventions

M1533 designed the required intervention channels:

```text
normal
reset_hidden_once_at_anchor
reset_hidden_every_step_from_anchor
zero_current_response_from_anchor
zero_action_history_from_anchor
delayed_hidden_8_at_anchor
delayed_hidden_16_at_anchor
wrong_history_donor_hidden_at_anchor
donor_response_action_stream_from_anchor
donor_response_action_plus_hidden_from_anchor
```

M1534 implemented and ran the bounded intervention smoke:

```text
accepted_pair_count: 3
target_side_count: 6
variant_count: 10
intervention_row_count: 60
anchor_replay_success_count: 60
anchor_replay_failure_count: 0
max_wrong_history_margin_gap: 0.02848063419634883
max_donor_response_action_margin_gap: 0.040193069514796065
success_drop_count: 0
passes_public_smoke_gates: true
passes_evidence_quality_targets: true
guardrail_violation_count: 0
```

M1535 audited the result as meaningful but source-small:

```text
wrong_history_verdict: preliminary_positive_source_small
donor_response_verdict: partial_positive_plus_hidden_response_only_weak
reset_zero_control_verdict: stronger_than_wrong_history
source_scope_verdict: source_small_t4_only_public_dev_rows
materialization_verdict: blocked
```

### M1536 Repeat Design

M1536 pre-registered a source-expanded repeat:

```text
source_seed: 1631
source_seed_count: 2
expected_source_row_count: 28
max_pair_candidates: 128
continuation_steps: 64
source-diversity gates: accepted pairs >= 6 and source-family edges >= 5
T5 handling: report and prefer at least one terminal-boundary accepted pair
control-dominance rule: reset/zero-current must not be collapsed into self-ID
```

This is the right next experiment because it directly tests the current blocker:
whether M1534 positives survive source expansion.

## Supported Claims

Supported:

```text
fresh ambiguity source planning can cover all intended public source families;
fixed-policy measured mining can find accepted matched pairs;
history intervention replay is deterministic enough for bounded public probes;
M1534 contains preliminary positive wrong-history and donor-response-plus-hidden
terminal-margin sensitivity;
M1536 defines a conservative source-expanded repeat before materialization.
```

## Unsupported Or Falsified Claims

Unsupported:

```text
source-expanded history-sensitivity repeat;
T5 or terminal-boundary history-sensitivity evidence;
success-drop evidence;
candidate materialization;
training corpus export;
paper-level evidence;
level3 anticipatory self-identification;
policy superiority.
```

Falsified for the current source-small evidence:

```text
M1534 alone is enough for candidate materialization;
T4-only positive rows can justify a terminal-boundary claim;
reset/zero-current effects can be treated as self-ID evidence.
```

## Failure Taxonomy Summary

Failure labels:

```text
scenario_sampling_failure
metric_artifact
```

`scenario_sampling_failure`:

```text
M1531/M1534 accepted only three measured pairs and all accepted pairs were T4.
No T5 or terminal-boundary pair has contributed accepted intervention evidence
yet.
```

`metric_artifact`:

```text
M1534 positives are real enough to repeat, but reset/zero-current controls have
larger maximum margin gaps. The branch must not treat control removal as
history necessity.
```

No contract violation, private holdout contamination, PPO washout, promotion
misuse, or training instability occurred in this branch.

## Public-Gate Overfit Risk

Risk:

```text
high
```

Reasons:

```text
all evidence is public development evidence;
M1534 used only three accepted measured pairs;
the branch has repeatedly adapted around public source-mining results;
T5/terminal-boundary rows remain absent from accepted intervention evidence;
the strongest absolute effect is still a reset/zero-current control.
```

This risk blocks materialization and paper-level claims. It does not block the
single pre-registered source-expanded repeat, because that repeat directly
reduces the overfit risk by expanding seeds and sources.

## Next Branch Decision

Continue the same branch to one bounded implementation milestone:

```text
m1538-paper-route-fresh-ambiguity-history-intervention-repeat-implementation
```

The implementation must follow M1536 exactly:

```text
source_seed: 1631
source_seed_count: 2
max_pair_candidates: 128
same ten intervention variants
no candidate materialization
route to result audit afterward
```

Stop conditions for the follow-up audit:

```text
accepted_pair_count < 6
accepted_source_family_edge_count < 5
T5/terminal-boundary rows absent and controls dominate
wrong-history and donor-plus-hidden positives do not source-expand
guardrail violation
```

If any stop condition fires, the audit should route to pair repair, task
generation, or branch synthesis instead of training.

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
m1538-paper-route-fresh-ambiguity-history-intervention-repeat-implementation
```
