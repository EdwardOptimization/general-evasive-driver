# M1518 Paper-Route Decisive History T5 Intervention Result Audit

## Summary

M1518 audits the M1517 bounded measured-intervention smoke.

Decision:

```text
t5_intervention_audit_null_effect_route_to_timing_amplification
```

M1517 is a clean plumbing pass and a null/weak intervention result. The
intervention module replayed all four admitted `t5_high_speed_close_obstacle`
targets, ran all seven variants, and produced complete artifacts with zero
guardrail violations. It did not produce an outcome-relevant history or response
ablation effect.

This audit keeps candidate materialization, corpus export, training, PPO,
promotion, private holdout, actor-input changes, and level3 self-identification
claims blocked.

## Evidence

Audited run:

```text
runs/m1517_decisive_history_t5_intervention_smoke
```

Summary:

```text
eligible_target_count: 4
variant_count: 7
intervention_row_count: 28
normal_row_count: 4
ablation_row_count: 24
wrong_history_row_count: 4
target_replay_failure_count: 0
donor_replay_failure_count: 0
max_margin_gap_from_normal: 0.016497911642290308
outcome_relevant_variant_count: 0
success_drop_count: 0
guardrail_violation_count: 0
```

Pair summary:

```text
close_wide             normal_margin 0.513292  max_gap 0.006793
drift_required_focus   normal_margin 0.566902  max_gap 0.010347
late_reveal_high_speed normal_margin 0.234235  max_gap 0.000570
low_mu_close           normal_margin 1.346516  max_gap 0.016498
```

All normal and ablated rollouts completed the obstacle with positive terminal
margin. The largest measured degradation came from `reset_hidden_every_step` on
`low_mu_close`, but it stayed below the pre-registered `0.02` margin-gap
threshold and did not produce a success drop.

## Variant-Level Audit

```text
variant                    mean_gap      max_gap      mean_action_l2  success_drops
reset_hidden_every_step    0.008552      0.016498     0.526171        0
reset_hidden_once          0.003340      0.006263     0.526171        0
zero_current_response      0.004829      0.010080     0.052283        0
delayed_hidden_8           0.000033      0.000101     0.006232        0
wrong_history_donor_hidden 0.000004      0.000031     0.012545        0
zero_action_history       -0.000113     -0.000008     0.004813        0
```

The result separates two signals:

```text
reset hidden changes the first action materially, but the scenarios absorb the
action change without outcome degradation;

wrong-donor hidden, delayed hidden, and zero action history barely move the
action or terminal margin under the decision-step intervention design.
```

This means M1517 cannot be used as self-identification evidence. It is evidence
about the current probe design: the rows and timing do not yet create a
decisive history-necessity test.

## Failure Taxonomy

Failure labels:

```text
scenario_sampling_failure
metric_artifact
```

`scenario_sampling_failure` applies because the admitted subset still has too
much post-decision slack for this intervention design. Even the most affected
row remains safely positive after reset-hidden intervention.

`metric_artifact` applies as a warning: treating replay success, complete
intervention artifacts, or sub-threshold margin movement as candidate evidence
would over-claim the result.

This is not a `contract_violation`, `training_instability`, `proof_washout`, or
`promotion_gate_failure`; no training or promotion occurred.

## Interpretation

M1518 supports:

```text
bounded intervention artifacts are complete and reproducible;
the current T5 decision-step intervention design is too weak or too late to
prove history necessity;
candidate materialization remains blocked.
```

M1518 does not support:

```text
level3 anticipatory self-identification;
source-diverse history necessity;
wrong-history causal dependence;
training corpus export;
promotion.
```

The likely causes are:

```text
1. intervention timing is late: the policy has already driven the car into a
   viable physical state by the decision step;
2. the selected rows retain enough terminal margin to absorb first-action
   differences;
3. current-frame ego response and scene geometry may dominate the local action;
4. donor hidden states across the four T5 modes may not be mismatched enough at
   the decision point.
```

## Decision

Do not materialize T5 candidates from M1517.

Do not train or run PPO from this result.

Route to a bounded timing-amplified intervention design:

```text
m1519-paper-route-decisive-history-t5-timing-amplified-intervention-design
```

The next design should test interventions that start earlier than the decision
step, for example from reveal, reveal-plus-k, or decision-minus-k windows. This
can answer whether history effects are washed out only because M1517 intervenes
too late. It must stay bounded, public, fixed-policy, no-training, no-corpus,
and no-promotion.

If timing amplification also produces null/weak effects, the branch should
prefer a synthesis or terminal-boundary retarget repair instead of more narrow
T5 intervention milestones.

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
m1519-paper-route-decisive-history-t5-timing-amplified-intervention-design
```
