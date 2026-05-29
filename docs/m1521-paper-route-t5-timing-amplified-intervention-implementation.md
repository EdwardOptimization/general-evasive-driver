# M1521 Paper-Route T5 Timing-Amplified Intervention Implementation

## Summary

M1521 implements and runs the bounded timing-amplified T5 intervention smoke
admitted by M1520.

Decision:

```text
t5_timing_amplified_intervention_smoke_positive_margin_route_to_audit
```

The smoke produced complete artifacts for four targets, four anchors, and seven
variants. Unlike M1517, earlier-window interventions produced outcome-relevant
margin gaps above the pre-registered `0.02` threshold. There were still no
success drops, and wrong-history donor hidden remained near-null. This is a
positive timing-amplification probe result, not yet candidate materialization or
level3 self-identification evidence.

## Implementation

New code:

```text
src/autodrift/decisive_history_t5_timing_interventions.py
tests/test_decisive_history_t5_timing_interventions.py
```

The implementation:

```text
uses the same four M1515-admitted t5_high_speed_close_obstacle targets;
replays deterministic fixed policy to named anchors;
switches only policy-side hidden/observation ablations at the anchor;
continues the simulator normally to terminal or bounded budget;
writes row, pair, anchor, guardrail, and summary artifacts;
does not clone or mutate hidden simulator state;
does not change the P0 actor observation contract.
```

## Smoke Command

```bash
PYTHONPATH=src python -m autodrift.decisive_history_t5_timing_interventions \
  --run-dir runs/m1521_t5_timing_amplified_intervention_smoke \
  --continuation-steps 64 \
  --device cpu
```

## Result

Run directory:

```text
runs/m1521_t5_timing_amplified_intervention_smoke
```

Summary:

```text
eligible_source_family: t5_high_speed_close_obstacle
eligible_target_count: 4
anchor_count: 4
variant_count: 7
intervention_row_count: 112
pair_row_count: 16
anchor_row_count: 4
normal_row_count: 16
ablation_row_count: 96
wrong_history_row_count: 16
target_replay_failure_count: 0
donor_replay_failure_count: 0
max_margin_gap_from_normal: 0.027952724375794435
max_first_action_l2: 0.5381348497698335
max_decision_state_delta_l2: 0.0996307537382291
outcome_relevant_variant_count: 9
divergence_relevant_variant_count: 46
success_drop_count: 0
guardrail_violation_count: 0
```

Focused tests:

```text
PYTHONPATH=src python -m pytest tests/test_decisive_history_t5_timing_interventions.py -q
5 passed
```

## Anchor Summary

```text
anchor            max_gap   max_state_delta  outcome_relevant  divergence_relevant
decision          0.016498  0.000000         0                 11
decision_minus_8  0.027953  0.099631         4                 12
reveal            0.027953  0.099631         4                 12
reveal_plus_4     0.022876  0.035828         1                 11
```

The result confirms the main M1519 hypothesis: moving intervention earlier than
the decision step increases measured margin degradation.

## Variant Interpretation

Outcome-relevant rows came from:

```text
reset_hidden_every_step_from_anchor
zero_current_response_from_anchor
```

Top rows:

```text
low_mu_close decision_minus_8 reset_hidden_every_step_from_anchor gap 0.027953
low_mu_close reveal reset_hidden_every_step_from_anchor gap 0.027953
drift_required_focus decision_minus_8 reset_hidden_every_step_from_anchor gap 0.023751
drift_required_focus reveal reset_hidden_every_step_from_anchor gap 0.023751
low_mu_close reveal_plus_4 reset_hidden_every_step_from_anchor gap 0.022876
low_mu_close decision_minus_8 zero_current_response_from_anchor gap 0.021038
low_mu_close reveal zero_current_response_from_anchor gap 0.021038
close_wide decision_minus_8 reset_hidden_every_step_from_anchor gap 0.020794
close_wide reveal reset_hidden_every_step_from_anchor gap 0.020794
```

Wrong-history donor hidden remained near-null:

```text
max wrong-history margin gap magnitude: about 0.000031
wrong-history success drops: 0
wrong-history action/state effects: near zero
```

This means M1521 is stronger than M1517 as an intervention-timing result, but it
still does not prove same-current wrong-history dependence or level3
self-identification.

## Interpretation

M1521 supports:

```text
decision-step intervention was too late to expose the available margin signal;
earlier reset/zero-current-response interventions can produce measurable
terminal-margin degradation;
the timing-amplified artifact path is now available for audit.
```

M1521 does not support:

```text
success-drop evidence;
wrong-history causal dependence;
candidate materialization;
training corpus export;
level3 anticipatory self-identification.
```

The correct next step is an audit, not training or materialization.

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
m1522-paper-route-t5-timing-amplified-intervention-result-audit
```
