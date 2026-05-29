# M1528 Paper-Route Fresh Ambiguity Source-Planner Implementation

## Summary

M1528 implements the bounded public fresh ambiguity source planner from M1527.

Decision:

```text
fresh_ambiguity_source_planner_smoke_pass_route_to_audit
```

The implementation adds:

```text
src/autodrift/fresh_ambiguity_source_mining.py
tests/test_fresh_ambiguity_source_mining.py
```

It runs a no-training, no-rollout, no-materialization planner smoke:

```text
runs/m1528_fresh_ambiguity_source_planner_smoke/summary.json
```

No policy training, PPO, replay, candidate materialization, corpus export,
private holdout, actor-input change, promotion, or self-identification claim is
made.

## Commands

Focused tests:

```bash
PYTHONPATH=src python -m pytest tests/test_fresh_ambiguity_source_mining.py -q
```

Result:

```text
6 passed
```

Smoke:

```bash
PYTHONPATH=src python -m autodrift.fresh_ambiguity_source_mining --output-dir runs/m1528_fresh_ambiguity_source_planner_smoke --seed 1528
```

Result:

```text
generated_source_specs=112
accepted_pair_candidates=112
passes_public_dry_gates=True
```

## Result Summary

```text
source_plan_count: 14
generated_source_specs: 112
accepted_pair_candidates: 112
unique_source_families: 14
unique_hidden_capability_pairs: 24
unique_geometry_keys: 42
unique_decision_steps: 20
max_single_source_family_share: 0.07142857142857142
closed_t5_subset_rows: 0
max_closed_t5_subset_share: 0.0
proxy_fault_family_count: 7
symmetric_proxy_fault_only: true
guardrail_violation_count: 0
passes_public_dry_gates: true
```

Proxy fault families:

```text
actuator_delay_step
brake_fade_or_loss_proxy
capability_step_down
capability_step_up
drive_loss_proxy
grip_loss_proxy
t4_actuator_delay_response
```

The planner explicitly treats these as symmetric single-track capability
proxies. It does not claim true one-wheel blowout, split-mu, half-shaft, or
individual-wheel failure modeling.

## Artifacts

```text
fresh_ambiguity_source_specs.csv
fresh_ambiguity_pair_candidates.csv
fresh_ambiguity_action_divergence.csv
fresh_ambiguity_rejected_pairs.csv
fresh_ambiguity_source_family_summary.csv
fresh_ambiguity_guardrail_summary.csv
fresh_ambiguity_trace_snapshots.csv
summary.json
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

## Interpretation

M1528 is a planner/infrastructure pass. It does not prove that the policy uses
history, and it does not produce measured rollout evidence. It does show that
the next measured branch can start from a source-diverse, guardrail-clean public
grid instead of the closed four-row T5 subset.

The next step should audit this planner smoke before any measured rollout or
candidate materialization.

## Next

```text
m1529-paper-route-fresh-ambiguity-source-planner-result-audit
```
