# M1517 Paper-Route Decisive History T5 Intervention Implementation

## Summary

M1517 implements and runs the bounded T5 measured-intervention smoke designed
in M1516.

Decision:

```text
t5_intervention_smoke_complete_null_effect_route_to_audit
```

The intervention plumbing worked cleanly, but the measured intervention effects
were below the pre-registered outcome-relevance threshold. This is a useful
null/weak result, not self-identification evidence.

This milestone does not materialize candidates, export a training corpus, run
replay gates, run PPO, train, promote, use private holdout, change actor
inputs, or claim level3 self-identification.

## Implementation

New code:

```text
src/autodrift/decisive_history_t5_interventions.py
tests/test_decisive_history_t5_interventions.py
```

The implementation:

```text
rebuilds the four eligible t5_high_speed_close_obstacle retarget specs;
deterministically replays the fixed M1362 policy to each decision step;
continues from the decision state with policy-side interventions;
does not clone or mutate hidden simulator state;
does not change the P0 actor observation contract.
```

## Smoke Command

```bash
PYTHONPATH=src python -m autodrift.decisive_history_t5_interventions \
  --run-dir runs/m1517_decisive_history_t5_intervention_smoke \
  --continuation-steps 64 \
  --device cpu
```

## Result

Run directory:

```text
runs/m1517_decisive_history_t5_intervention_smoke
```

Summary:

```text
eligible_source_family: t5_high_speed_close_obstacle
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

Focused tests:

```text
PYTHONPATH=src python -m pytest tests/test_decisive_history_t5_interventions.py -q
6 passed
```

## Pair Summary

```text
candidate_id                                           normal_margin  max_gap  success_drop
t5_high_speed_close_obstacle-000-close_wide                 0.513     0.0068  none
t5_high_speed_close_obstacle-000-low_mu_close                1.347     0.0165  none
t5_high_speed_close_obstacle-000-late_reveal_high_speed      0.234     0.0006  none
t5_high_speed_close_obstacle-000-drift_required_focus        0.567     0.0103  none
```

The largest measured degradation came from `reset_hidden_every_step` on the
`low_mu_close` row, but it remained below the pre-registered `0.02` margin-gap
threshold and did not create a success drop.

## Interpretation

M1517 proves:

```text
bounded measured-intervention plumbing works for the admitted T5 high-speed
subset;
normal/reset/zero/delayed/wrong-donor-hidden rows can be measured with complete
artifacts;
the current intervention setup did not reveal outcome-relevant history
sensitivity on this subset.
```

M1517 does not prove:

```text
level3 self-identification;
source-diverse history necessity;
candidate materialization validity;
policy superiority.
```

The result should be audited as a null/weak intervention result. Possible
explanations include:

```text
the intervention starts too late;
the T5 rows are still too stable under the current actor;
the donor-hidden wrong-history intervention is too weak because current
observation dominates;
the selected subset is useful for reactive avoidance but not for history
necessity.
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
m1518-paper-route-decisive-history-t5-intervention-result-audit
```

M1518 should decide whether to:

```text
repair/amplify the intervention timing;
retarget even closer to the terminal boundary;
shift to finite-window/current-response comparison on these rows;
or close this T5 subset as a null self-ID probe.
```
