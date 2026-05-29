# M1524 Paper-Route T5 Response Mismatch Intervention Implementation

## Summary

M1524 implements and runs the response/action-history mismatch smoke designed in
M1523.

Decision:

```text
t5_response_mismatch_smoke_donor_null_zero_current_positive_route_to_audit
```

The diagnostic ran cleanly, with high donor response mismatch strength and zero
replay failures. The donor response/action stream variants were near-null. The
only outcome-relevant rows came from the `zero_current_response_from_anchor`
control. This is a strong negative result for the current donor response
mismatch design and reinforces that M1521's positive margin gaps were response
removal/timing sensitivity, not wrong-history self-identification.

## Implementation

New code:

```text
src/autodrift/decisive_history_t5_response_mismatch.py
tests/test_decisive_history_t5_response_mismatch.py
```

The implementation:

```text
preserves target scene context indices 12:72;
perturbs only P0 response/action-history indices 0:12;
records donor response mismatch strength;
keeps deployed actor contract unchanged;
does not materialize candidates, export corpus, train, run PPO, promote, or use
private holdout.
```

## Smoke Command

```bash
PYTHONPATH=src python -m autodrift.decisive_history_t5_response_mismatch \
  --run-dir runs/m1524_t5_response_mismatch_intervention_smoke \
  --continuation-steps 64 \
  --device cpu
```

## Result

Run directory:

```text
runs/m1524_t5_response_mismatch_intervention_smoke
```

Summary:

```text
eligible_source_family: t5_high_speed_close_obstacle
eligible_target_count: 4
anchor_count: 3
variant_count: 7
intervention_row_count: 84
pair_row_count: 12
anchor_row_count: 3
variant_row_count: 7
normal_row_count: 12
mismatch_row_count: 72
target_replay_failure_count: 0
donor_replay_failure_count: 0
max_margin_gap_from_normal: 0.021037607967195893
max_first_action_l2: 0.07314944555537312
max_donor_response_l2_mean: 0.4977846671714798
outcome_relevant_variant_count: 2
divergence_relevant_variant_count: 13
success_drop_count: 0
guardrail_violation_count: 0
```

Focused tests:

```text
PYTHONPATH=src python -m pytest tests/test_decisive_history_t5_response_mismatch.py -q
6 passed
```

## Variant Summary

```text
variant                                      max_gap    max_action_l2  mean_donor_l2
donor_response_action_plus_hidden_from_anchor 0.000443  0.058327       0.264972
donor_response_action_stream_from_anchor      0.000401  0.036106       0.264972
donor_ego_response_stream_from_anchor         0.000410  0.035456       0.265045
donor_action_history_stream_from_anchor       0.000008  0.000661       0.265729
donor_response_current_frame_at_anchor        0.000029  0.036106       0.265837
zero_current_response_from_anchor             0.021038  0.073149       0.000000
```

The donor mismatch was real by input distance, but it did not produce meaningful
margin gaps.

## Anchor Summary

```text
anchor            max_gap   outcome_relevant  divergence_relevant
decision          0.010080  0                 5
decision_minus_8  0.021038  1                 4
reveal            0.021038  1                 4
```

Outcome-relevant rows came only from `zero_current_response_from_anchor` on
`low_mu_close` at `decision_minus_8` and `reveal`.

## Interpretation

M1524 supports:

```text
the response/action mismatch harness works and preserves target scene context;
donor response mismatch strength is nontrivial;
current response removal still creates small margin degradation in the strongest
T5 low-mu rows.
```

M1524 does not support:

```text
donor response/action mismatch causes wrong behavior;
wrong-history self-identification;
candidate materialization;
training corpus export;
level3 self-identification.
```

The key result is negative:

```text
even when donor response/action stream differs from target response/action
stream, the policy behavior is mostly unchanged under this T5 setup.
```

This could mean the current T5 rows are still dominated by current scene context,
the donor modes are not adversarial enough, or the actor is not strongly using
the response stream in a way that this intervention exposes.

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
m1525-paper-route-t5-response-mismatch-result-audit
```
