# M1539 Paper-Route Fresh Ambiguity History-Intervention Repeat Result Audit

## Summary

M1539 audits the M1538 source-expanded history-intervention repeat.

Decision:

```text
fresh_ambiguity_repeat_audit_positive_nonterminal_route_terminal_boundary_repair
```

M1538 is a real source-expanded positive result for wrong-history and
donor-response-plus-hidden margin sensitivity. It is not enough for candidate
materialization because the positive rows still do not include T5 or
terminal-boundary history-positive target sides, and direct donor
response/action-stream sensitivity remains below the pre-registered threshold.

No candidate materialization, corpus export, training, PPO, promotion, private
holdout, actor-input change, or level3 self-identification claim is admitted.

## Audited Evidence

Artifacts:

```text
runs/m1538_fresh_ambiguity_measured_mining_repeat/summary.json
runs/m1538_fresh_ambiguity_history_intervention_repeat/summary.json
docs/m1538-paper-route-fresh-ambiguity-history-intervention-repeat-implementation.md
```

Source expansion:

```text
source_row_count: 28
attempted_source_families: 14
reached_decision_source_families: 14
measured_pair_candidate_count: 18
accepted_measured_pair_count: 13
accepted_source_family_edge_count: 11
accepted_source_family_max_share: 0.11538461538461539
t5_or_terminal_boundary_accepted_pair_count: 5
```

Interventions:

```text
accepted_pair_count: 13
target_side_count: 26
intervention_row_count: 260
anchor_replay_success_count: 260
anchor_replay_failure_count: 0
max_wrong_history_margin_gap: 0.12242202469492369
max_donor_response_action_margin_gap: 0.12600996295198996
max_reset_zero_margin_gap: 0.09327067729080696
control_to_history_gap_ratio: 0.7401849433631154
success_drop_count: 12
guardrail_violation_count: 0
```

## Verdicts

### Source Diversity

Verdict:

```text
pass
```

M1538 passes the M1536 source-diversity gates:

```text
accepted_measured_pair_count >= 6
accepted_source_family_edge_count >= 5
accepted_source_family_max_share <= 0.50
t5_or_terminal_boundary_accepted_pair_count >= 1
anchor_replay_failure_count == 0
```

### History Sensitivity

Verdict:

```text
positive_source_expanded_nonterminal
```

Evidence:

```text
wrong_history_donor_hidden_at_anchor:
  positive_target_sides: 4
  positive_pairs: 4
  positive_source_edges: 3
  max_margin_gap_from_normal: 0.12242202469492369

donor_response_action_plus_hidden_from_anchor:
  positive_target_sides: 4
  positive_pairs: 4
  positive_source_edges: 3
  max_margin_gap_from_normal: 0.12600996295198996
  success_drop_count: 1

delayed_hidden_16_at_anchor:
  positive_target_sides: 2
  positive_source_edges: 2
  max_margin_gap_from_normal: 0.038692235106069006
```

This is stronger than M1534 and is not a single-pair artifact.

### Control Dominance

Verdict:

```text
not_dominant_by_max_gap
```

Evidence:

```text
max_reset_zero_margin_gap: 0.09327067729080696
max_history_margin_gap: 0.12600996295198996
control_to_history_gap_ratio: 0.7401849433631154
```

Controls still matter and produce success drops, but the maximum terminal-margin
effect is now in the history/donor-plus-hidden channel rather than the
reset/zero-current channel.

### T5 / Terminal Boundary

Verdict:

```text
blocked_absent_history_positive
```

Evidence:

```text
t5_or_terminal_boundary_accepted_pair_count: 5
wrong_history_positive_t5_or_boundary_target_sides: 0
donor_plus_hidden_positive_t5_or_boundary_target_sides: 0
```

This is the current blocker. Source expansion reached T5/terminal-boundary
pairs, but the history-positive rows still came from non-terminal pairs.

### Donor Response/Action Stream

Verdict:

```text
weak_below_threshold
```

Evidence:

```text
donor_response_action_stream_from_anchor:
  positive_target_sides: 0
  max_margin_gap_from_normal: 0.019388015986013585
```

The plus-hidden effect is strong, while stream-only intervention remains just
below threshold. This supports continued history-intervention study, not a
deployment-level self-ID claim.

## Materialization Verdict

Verdict:

```text
blocked
```

Reasons:

```text
T5/terminal-boundary history-positive target sides remain zero;
donor response/action stream alone remains below threshold;
the result is public development evidence;
no audit has defined candidate source-family caps or training use;
level3 self-identification remains unsupported.
```

M1538 can be retained as a public diagnostic surface. It should not be converted
into a training corpus yet.

## Next Route

Admit terminal-boundary repair design:

```text
m1540-paper-route-terminal-boundary-history-positive-source-repair-design
```

The next design should target:

```text
t5_near_boundary_warmup
t5_high_speed_close_obstacle
t5_boundary_axis_retarget
late_reveal_boundary
curved_boundary_obstacle
```

It should explicitly repair the missing link:

```text
accepted terminal-boundary pair
  -> wrong-history or donor-plus-hidden terminal-margin gap >= 0.02
  -> preferably success drop or collision/clearance outcome change
```

The design must keep M1538's non-terminal positives as supporting context, not
as a substitute for terminal-boundary evidence.

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
m1540-paper-route-terminal-boundary-history-positive-source-repair-design
```
