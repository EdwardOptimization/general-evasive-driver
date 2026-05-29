# M1522 Paper-Route T5 Timing-Amplified Intervention Result Audit

## Summary

M1522 audits the M1521 timing-amplified intervention smoke.

Decision:

```text
t5_timing_audit_positive_margin_wrong_history_null_route_to_response_mismatch_design
```

M1521 is a real improvement over M1517: earlier interventions produced
outcome-relevant terminal-margin degradation above the pre-registered `0.02`
threshold. However, the positive rows came from reset-hidden and
zero-current-response variants. Wrong-history donor hidden remained near-null,
and there were no success drops. Therefore M1521 is positive timing-sensitivity
evidence, not candidate-materialization or level3 self-identification evidence.

The next route should strengthen the wrong-history diagnostic itself by
designing response/action-history mismatch interventions. Boundary tightening
can come later if a wrong-history or response-mismatch variant produces a
nontrivial margin gap.

## Audited Evidence

Audited run:

```text
runs/m1521_t5_timing_amplified_intervention_smoke
```

Summary:

```text
eligible_target_count: 4
anchor_count: 4
variant_count: 7
intervention_row_count: 112
pair_row_count: 16
anchor_row_count: 4
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

Anchor summary:

```text
decision          max_gap 0.016498  outcome_relevant 0
decision_minus_8  max_gap 0.027953  outcome_relevant 4
reveal            max_gap 0.027953  outcome_relevant 4
reveal_plus_4     max_gap 0.022876  outcome_relevant 1
```

This supports the timing hypothesis: decision-step intervention was too late to
expose the available margin signal, while reveal and decision-minus-8 anchors
are more sensitive.

## Positive Signal

Outcome-relevant variants:

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

This proves the intervention system can now perturb policy behavior early enough
to change terminal margin. It is a useful probe result.

## Limitation

Wrong-history donor hidden remained near-null:

```text
max wrong-history gap magnitude: about 0.000031
wrong-history success drops: 0
wrong-history action/state effects: near zero
```

No success drops occurred for any variant:

```text
success_drop_count: 0
```

Therefore the result cannot support:

```text
candidate materialization;
training corpus export;
same-current wrong-history dependence;
level3 anticipatory self-identification.
```

## Failure Taxonomy

Failure labels:

```text
scenario_sampling_failure
metric_artifact
```

`scenario_sampling_failure` remains because the rows still have enough terminal
margin to avoid success drops. It is weaker than M1517 because margin gaps now
exist, but it is not solved.

`metric_artifact` remains because treating reset/zero-current timing sensitivity
as self-identification would over-claim the evidence.

No contract violation, private holdout contamination, PPO washout, or promotion
gate misuse occurred.

## Decision

Do not materialize candidates.

Do not export a training corpus.

Do not run PPO or train from M1521.

Route to a stricter wrong-history / response-mismatch design:

```text
m1523-paper-route-t5-response-mismatch-intervention-design
```

The next design should test whether the actor depends on the response/action
stream, not just whether reset hidden or zero current response can reduce
margin. Candidate designs include:

```text
donor_response_current_frame:
  replace response/action indices 0-11 with donor response while keeping target
  scene context;

donor_response_window:
  replay donor response/action frames across a short window while target
  physical state evolves normally;

action_response_mismatch:
  keep target scene and target current kinematics, but mismatch previous
  physical commands or actuator response from donor history;

stronger_wrong_hidden:
  combine donor hidden with donor response/action stream, while recording this
  as diagnostic intervention rather than deployable input.
```

This is still diagnostic intervention work. It must preserve the P0 deployed
actor contract and stay no-training/no-materialization until audited.

If response-mismatch remains null, then terminal-boundary retargeting alone is
unlikely to prove wrong-history self-ID and the branch should synthesize or
close the current T5 subset.

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
m1523-paper-route-t5-response-mismatch-intervention-design
```
