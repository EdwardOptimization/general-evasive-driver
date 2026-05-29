# M1554 Paper-Route Pair-Expanded Intervention Result Audit

## Summary

M1554 audits the M1553 pair-expanded calibrated intervention smoke.

Decision:

```text
pair_expanded_intervention_audit_history_null_route_temporal_active_set_redesign
```

M1553 separated two facts cleanly:

```text
public smoke / replay reliability: pass
history-sensitive mechanism evidence: null
```

This is important. The M1547 pair bottleneck has been repaired, so the null
result can no longer be explained only by source-family concentration. The more
likely issue is that the selected anchors are not in a temporal active set where
history perturbations can still change terminal outcome. Another direct replay
over the same M1550 anchors is not justified.

No candidate materialization, training corpus export, training, PPO, promotion,
private holdout, actor-input change, or level3 self-identification claim is
admitted.

## Evidence

M1553 public/replay evidence:

```text
accepted_pair_count: 21
accepted_source_family_edge_count: 5
max_single_pair_source_edge_share: 0.38095238095238093
max_endpoint_share: 0.14285714285714285
accepted_window_bucket_count: 3
target_side_count: 42
intervention_row_count: 420
anchor_replay_failure_count: 0
missing_spec_count: 0
passes_public_smoke_gates: true
```

M1553 history evidence:

```text
terminal_wrong_history_positive_target_sides: 0
terminal_donor_plus_hidden_positive_target_sides: 0
terminal_donor_stream_positive_target_sides: 0
terminal_wrong_or_donor_success_drop_count: 0
terminal_max_history_margin_gap: 0.00025038157254009263
terminal_max_control_margin_gap: 0.00003099723002852883
passes_history_positive_gates: false
passes_evidence_quality_targets: false
```

Variant maxima were all tiny:

```text
wrong_history_donor_hidden_at_anchor: 0.000241753384175869
donor_response_action_plus_hidden_from_anchor: 0.00025038157254009263
donor_response_action_stream_from_anchor: 0.00006257579068158492
zero_current_response_from_anchor: 0.00003099723002852883
```

## Verdicts

Public smoke verdict:

```text
pass
```

History evidence verdict:

```text
null
```

Current pair-bottleneck verdict:

```text
repaired_not_sufficient
```

The source and pair construction now works well enough to test the mechanism.
The mechanism did not appear at the tested anchors.

## Supported Claims

Supported:

```text
pair-expanded replay infrastructure is reliable;
M1550/M1553 accepted pair reconstruction is deterministic;
source-edge and endpoint diagnostics are available and not concentrated enough
  to explain away the null result;
public replay pass alone is not evidence of self-identification.
```

## Unsupported Or Falsified Claims

Unsupported:

```text
history necessity on M1550 pair-expanded terminal-boundary anchors;
wrong-history success drops;
donor response/action stream sensitivity;
candidate materialization;
training corpus export;
paper-level evidence;
level3 anticipatory self-identification.
```

Falsified for the current anchors:

```text
the M1547 null result was only caused by too few accepted pairs;
M1550 pair-expanded anchors are sufficient to produce terminal-boundary
wrong-history sensitivity;
another direct replay over the same anchors is likely to change the conclusion.
```

## Failure Classification

Failure type:

```text
metric_artifact
```

The artifact risk is interpretive: a replay/public-gate pass can look like
progress, but the mechanism metric is null. The result should be preserved as a
negative mechanism result, not repaired by lowering the history threshold.

## Next Route

Admit one design milestone:

```text
m1555-paper-route-temporal-active-set-redesign-design
```

The next route must change the source/anchor criterion before replay:

```text
select anchors where small action perturbations can still change terminal
  margin or success;
prefer earlier pre-commitment anchors over post-decision anchors when possible;
require local action-sensitivity before wrong-history intervention;
report whether the fixed policy is already in a terminally stable basin;
keep all actor inputs unchanged.
```

This is not an admission to train or materialize. It is only an admission to
design a stronger no-training source/anchor miner.

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
