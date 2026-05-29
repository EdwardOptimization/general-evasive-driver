# M1534 Paper-Route Fresh Ambiguity History-Intervention Implementation

## Summary

M1534 implements the bounded history-intervention runner from M1533 and runs one
public smoke over the M1531 accepted measured pairs.

Decision:

```text
fresh_ambiguity_history_intervention_smoke_positive_route_to_audit
```

The implementation adds:

```text
src/autodrift/fresh_ambiguity_history_interventions.py
tests/test_fresh_ambiguity_history_interventions.py
```

Smoke artifact:

```text
runs/m1534_fresh_ambiguity_history_intervention_smoke/summary.json
```

No candidate materialization, corpus export, training, PPO, promotion, private
holdout, actor-input change, or self-identification claim is made.

## Commands

Focused tests:

```bash
PYTHONPATH=src python -m pytest tests/test_fresh_ambiguity_history_interventions.py -q
```

Result:

```text
6 passed
```

Smoke:

```bash
PYTHONPATH=src python -m autodrift.fresh_ambiguity_history_interventions --output-dir runs/m1534_fresh_ambiguity_history_intervention_smoke --seed 1534
```

Result:

```text
intervention_row_count=60
passes_public_smoke_gates=True
```

## Result Summary

```text
accepted_pair_count: 3
target_side_count: 6
variant_count: 10
intervention_row_count: 60
pair_summary_row_count: 6
anchor_replay_success_count: 60
anchor_replay_failure_count: 0
wrong_history_row_count: 6
donor_response_action_row_count: 12
reset_zero_control_row_count: 24
max_margin_gap_from_normal: 0.18265487369979994
max_wrong_history_margin_gap: 0.02848063419634883
max_donor_response_action_margin_gap: 0.040193069514796065
success_drop_count: 0
passes_public_smoke_gates: true
passes_evidence_quality_targets: true
guardrail_violation_count: 0
```

Variant summary:

```text
wrong_history_donor_hidden_at_anchor:
  max_margin_gap_from_normal: 0.02848063419634883
  max_first_action_l2: 0.25329317152326886

donor_response_action_plus_hidden_from_anchor:
  max_margin_gap_from_normal: 0.040193069514796065
  max_first_action_l2: 0.278522876362962

donor_response_action_stream_from_anchor:
  max_margin_gap_from_normal: 0.006656528888189683
  max_first_action_l2: 0.1180114082746747

reset_hidden_every_step_from_anchor:
  max_margin_gap_from_normal: 0.18265487369979994
  max_first_action_l2: 0.475699535131027

zero_action_history_from_anchor:
  max_margin_gap_from_normal: 0.10665914868873116
  max_first_action_l2: 0.0990002746743262

zero_current_response_from_anchor:
  max_margin_gap_from_normal: 0.02174461234102054
  max_first_action_l2: 0.24430144974384213
```

Pair-level positive rows:

```text
pair-0000 left:
  wrong_history gap: 0.02848063419634883
  donor_response_action max gap: 0.040193069514796065

pair-0002 right:
  wrong_history gap: 0.026003752363084942
  donor_response_action max gap: 0.030347164618969913
```

## Interpretation

M1534 is the first fresh-ambiguity measured intervention smoke where
wrong-history and donor response/action channels both show outcome-relevant
terminal-margin gaps above the pre-registered `0.02` threshold.

This is promising, but not yet a paper-level or level3 self-identification
claim:

```text
source count is still small;
accepted measured pairs are public development pairs;
success_drop_count is 0;
reset/zero-current controls also produce larger effects;
the result needs an audit before any materialization or stronger claim.
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
m1535-paper-route-fresh-ambiguity-history-intervention-result-audit
```
