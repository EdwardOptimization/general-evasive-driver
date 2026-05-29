# M1585 Paper-Route Source-Diverse Pairability History-Intervention Implementation

## Summary

M1585 implements and runs the bounded source-diverse pairability-grounded
history-intervention smoke designed in M1584.

Decision:

```text
source_diverse_pairability_history_intervention_smoke_public_pass_control_dominated_route_to_audit
```

The implementation is live and public gates pass. The evidence-quality targets
do not pass because current-frame/control ablations dominate the observed
history effects.

This is useful negative evidence:

```text
pairability is not enough;
source-diverse wrong-history effects exist;
but current-frame/action-history controls explain too much of the outcome change.
```

Do not treat M1585 as history necessity, self-identification, materialization,
or training evidence.

## Implementation

New module:

```text
src/autodrift/source_diverse_pairability_history_interventions.py
```

Focused tests:

```text
tests/test_source_diverse_pairability_history_interventions.py
```

Focused test result:

```text
PYTHONPATH=src python -m pytest tests/test_source_diverse_pairability_history_interventions.py -q
3 passed
```

The implementation:

```text
selects tier-A M1582 pairability rows with source-edge/window/family caps;
evaluates both target-donor directions;
runs normal, wrong-history, donor-response/action, reset, zero-current, zero-action, and zero-all variants;
reports public gates, evidence-quality targets, and null classification;
keeps high-speed endpoint coverage diagnostic-only;
does not train, run PPO, materialize candidates, export corpus, or promote.
```

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.source_diverse_pairability_history_interventions --output-dir runs/m1585_source_diverse_pairability_history_intervention_smoke --pair-rows runs/m1582_history_pairability_source_miner_smoke/pairability_pair_rows.csv --seed 1901 --seed-count 6 --max-source-specs 480 --max-anchor-candidates 640 --target-pairs 72 --continuation-steps 64
```

## Result

Artifact:

```text
runs/m1585_source_diverse_pairability_history_intervention_smoke/summary.json
```

Public gates:

```text
selected_pair_count: 72
selected_source_edge_count: 19
selected_endpoint_source_family_count: 7
selected_window_count: 6
max_selected_source_edge_share: 0.05555555555555555
same_window_selected_pair_count: 72
directed_pair_count: 144
intervention_row_count: 1152
anchor_replay_failure_count: 0
passes_public_smoke_gates: true
```

Evidence metrics:

```text
history_positive_directed_pair_count: 23
history_positive_source_edge_count: 8
history_positive_endpoint_source_family_count: 7
history_success_drop_count: 0
max_history_margin_gap: 0.12908281005342204
max_current_frame_control_gap: 0.3274137328831479
control_substitution_dominated_share: 0.7184466019417476
passes_evidence_quality_targets: false
null_result_classification: control_dominated
```

High-speed and late-reveal endpoint diagnostics:

```text
high_speed_endpoint_directed_pair_count: 0
late_reveal_endpoint_directed_pair_count: 0
```

The high-speed result is not a new failure; M1583 already scoped high-speed as
diagnostic-only because the capped M1582 top pair set had no high-speed
endpoint pairs.

## Variant Summary

```text
wrong_history_hidden max gap: 0.10436934117322849
donor_response_action_plus_hidden max gap: 0.12908281005342204
donor_response_action_only max gap: 0.011708876431510973
reset_hidden max gap: 0.01229398408470983
zero_action_history max gap: 0.3274137328831479
zero_current_response max gap: 0.07821424364900809
zero_all_response max gap: 0.07821424364900809
```

The important observation is not that history has no effect. It does: there are
`23` history-positive directed pairs and `8` positive source edges. The blocker
is that zero-action/current-frame controls are stronger on many groups, and no
history variant produces a unique success drop.

## Supported Claims

M1585 supports:

```text
the M1582 pairability set can drive a source-diverse intervention harness;
the intervention harness can run 1152 public rows with zero anchor replay failures;
wrong-history and donor-plus-hidden variants produce nontrivial margin changes;
the current selected task family is control-dominated, so pairability alone is not enough.
```

## Unsupported Claims

M1585 does not support:

```text
history necessity;
source-diverse self-identification;
high-speed history sensitivity;
candidate materialization;
training corpus export;
PPO continuation;
checkpoint promotion;
private-holdout evidence;
paper-level result;
level3 anticipatory self-identification.
```

## Failure Taxonomy

```text
objective_overfit
```

The harness and source diversity worked. The evidence objective is still too
easy for current-frame/action-history ablations to satisfy or dominate.

## Route Decision

M1586 must audit before any next implementation. The audit should decide whether
the right next step is:

```text
stricter selection near history-vs-control active set;
variant redesign that isolates hidden-state history from zero-action/current-frame effects;
source repair for late/high-speed endpoints;
or branch synthesis if the current pairability branch is drifting into public-row gate optimization.
```

## Guardrails

```text
history_interventions_executed: true
candidate_materialized: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
training_corpus_exported: false
labels_enter_actor_input: false
level3_self_id_claim_made: false
guardrail_violation_count: 0
```

## Next

```text
m1586-paper-route-source-diverse-pairability-intervention-result-audit
```
