# M1535 Paper-Route Fresh Ambiguity History-Intervention Result Audit

## Summary

M1535 audits the M1534 bounded history-intervention smoke.

Decision:

```text
fresh_ambiguity_history_intervention_audit_positive_source_small_admit_repeat_design
```

M1534 is a meaningful positive smoke: both wrong-history hidden injection and
donor response/action-plus-hidden injection produced terminal-margin gaps above
the pre-registered `0.02` evidence target. The result is still too small and too
control-sensitive for candidate materialization or level3 self-identification
claims.

No candidate materialization, corpus export, training, PPO, promotion, private
holdout, actor-input change, or self-identification claim is admitted.

## Audited Evidence

Artifact:

```text
runs/m1534_fresh_ambiguity_history_intervention_smoke/summary.json
```

Key results:

```text
accepted_pair_count: 3
target_side_count: 6
variant_count: 10
intervention_row_count: 60
anchor_replay_success_count: 60
anchor_replay_failure_count: 0
wrong_history_row_count: 6
donor_response_action_row_count: 12
reset_zero_control_row_count: 24
max_wrong_history_margin_gap: 0.02848063419634883
max_donor_response_action_margin_gap: 0.040193069514796065
success_drop_count: 0
passes_public_smoke_gates: true
passes_evidence_quality_targets: true
guardrail_violation_count: 0
```

## Channel Verdicts

### Wrong-History Hidden

Verdict:

```text
preliminary_positive
```

Evidence:

```text
wrong_history_donor_hidden_at_anchor:
  row_count: 6
  max_margin_gap_from_normal: 0.02848063419634883
  max_first_action_l2: 0.25329317152326886
  success_drop_count: 0
```

Positive target sides:

```text
pair-0000 left:
  max_wrong_history_margin_gap: 0.02848063419634883

pair-0002 right:
  max_wrong_history_margin_gap: 0.026003752363084942
```

This supports a repeat/expansion route. It does not yet support candidate export
or level3 self-identification.

### Donor Response/Action

Verdict:

```text
mixed_positive
```

Evidence:

```text
donor_response_action_plus_hidden_from_anchor:
  max_margin_gap_from_normal: 0.040193069514796065
  max_first_action_l2: 0.278522876362962

donor_response_action_stream_from_anchor:
  max_margin_gap_from_normal: 0.006656528888189683
  max_first_action_l2: 0.1180114082746747
```

Interpretation:

```text
donor response/action plus donor hidden is positive;
donor response/action stream alone is weaker.
```

This suggests that the recurrent hidden channel matters in these rows, but the
effect still needs source-diverse repeat evidence and controls.

### Reset / Zero-Current Controls

Verdict:

```text
strong_control_effect
```

Evidence:

```text
reset_hidden_every_step_from_anchor:
  max_margin_gap_from_normal: 0.18265487369979994

zero_action_history_from_anchor:
  max_margin_gap_from_normal: 0.10665914868873116

zero_current_response_from_anchor:
  max_margin_gap_from_normal: 0.02174461234102054
```

This is important: control interventions are stronger than wrong-history on the
current small set. M1534 therefore cannot be used as a strong self-ID claim. The
next experiment must preserve this channel separation.

## Source Scope

Accepted pairs:

```text
pair-0000:
  t4_staged_warmup_capability -> t4_actuator_delay_response

pair-0002:
  t4_actuator_delay_response -> capability_step_up

pair-0006:
  capability_step_down -> capability_step_up
```

Scope limitations:

```text
accepted_pair_count is only 3;
all accepted pairs are T4;
no T5 terminal-boundary pair contributed accepted intervention evidence;
success_drop_count is 0;
all rows are public development rows;
private holdout is not used.
```

## Materialization Verdict

Verdict:

```text
blocked
```

Reasons:

```text
source-small;
T4-only accepted pair set;
reset/zero-current controls dominate max margin gap;
no success drops;
no repeat or source-expanded evidence yet.
```

## Next Route

Admit source-expanded repeat design:

```text
m1536-paper-route-fresh-ambiguity-history-intervention-repeat-design
```

The repeat design should:

```text
increase source_seed_count to at least 2;
preserve all 14 source families;
prefer more accepted T5 / terminal-boundary pairs;
run the same intervention channels;
pre-register a stronger source-diversity pass criterion;
keep candidate materialization blocked until repeat audit.
```

The next claim target should be:

```text
source-expanded preliminary history-sensitivity repeat
```

not:

```text
level3 self-identification
paper-level evidence
candidate materialization
```

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
m1536-paper-route-fresh-ambiguity-history-intervention-repeat-design
```
