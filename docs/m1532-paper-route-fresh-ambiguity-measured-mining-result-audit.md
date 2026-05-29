# M1532 Paper-Route Fresh Ambiguity Measured-Mining Result Audit

## Summary

M1532 audits the M1531 bounded measured-mining smoke.

Decision:

```text
fresh_ambiguity_measured_mining_audit_admit_history_intervention_design
```

M1531 is a clean measured-mining plumbing pass and it found measured pair
candidates. It is not candidate-export or self-identification evidence because
wrong-history and donor response/action continuations were not executed.

No candidate materialization, corpus export, training, PPO, promotion, private
holdout, actor-input change, or self-ID claim is admitted.

## Audited Evidence

Artifact:

```text
runs/m1531_fresh_ambiguity_measured_mining_smoke/summary.json
```

Key results:

```text
source_row_count: 14
attempted_source_families: 14
reached_reveal_source_families: 14
reached_decision_source_families: 13
trace_row_count: 1226
snapshot_row_count: 68
measured_pair_candidate_count: 10
accepted_measured_pair_count: 3
intervention_row_count: 10
target_replay_failure_count: 1
donor_replay_failure_count: 0
max_single_source_family_share: 0.07142857142857142
max_closed_t5_subset_share: 0.0
proxy_fault_family_count: 7
history_interventions_executed: false
passes_public_smoke_gates: true
passes_evidence_quality_targets: false
guardrail_violation_count: 0
```

## Verdicts

### Measured Plumbing

Verdict:

```text
pass
```

M1531 wrote measured traces, snapshots, pair candidates, intervention placeholder
rows, source-family summary, guardrail summary, and summary JSON. The smoke used
the fixed public checkpoint and kept the actor contract unchanged.

### Source Diversity

Verdict:

```text
pass_for_intervention_design
```

Reasons:

```text
14 source families attempted;
13 source families reached decision;
closed T5 subset share is 0.0;
7 proxy-fault families are represented;
max single-source share is 0.0714.
```

This is enough to design history interventions over the measured pairs.

### Measured Pair Quality

Verdict:

```text
partial_pass
```

M1531 produced:

```text
measured_pair_candidate_count: 10
accepted_measured_pair_count: 3
```

This is enough for a bounded intervention design. It is not enough for candidate
export or paper-level claims.

### History-Intervention Evidence

Verdict:

```text
missing
```

M1531 did not execute:

```text
wrong_history_donor_hidden_at_anchor
donor_response_action_stream_from_anchor
delayed_hidden_8_or_16_at_anchor
zero_current_response / zero_action_history controls over accepted pairs
```

Therefore:

```text
passes_evidence_quality_targets: false
```

This is the active blocker.

## Failure Taxonomy

Use:

```text
none:
  public measured plumbing passed and guardrails were clean.

metric_artifact risk:
  measured pair acceptance may depend on relaxed proxy distances and normal
  measured pairs only. This is not yet a failure, but it must be controlled in
  the intervention design.
```

No contract violation, private holdout contamination, training instability, or
promotion misuse occurred.

## Next Route

Admit history-intervention design:

```text
m1533-paper-route-fresh-ambiguity-history-intervention-design
```

M1533 should design bounded continuations for the M1531 accepted measured pairs:

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
```

The design must keep three claim channels separate:

```text
reset/zero-current sensitivity;
wrong-history sensitivity;
donor response/action sensitivity.
```

Only wrong-history or donor response/action outcome degradation under matched
scene/current-state can support later history-necessity claims.

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
m1533-paper-route-fresh-ambiguity-history-intervention-design
```
