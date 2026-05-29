# M1531 Paper-Route Fresh Ambiguity Measured-Mining Implementation

## Summary

M1531 implements the bounded measured fixed-policy source miner designed by
M1530.

Decision:

```text
fresh_ambiguity_measured_mining_smoke_pass_history_interventions_missing_route_to_audit
```

The implementation adds:

```text
src/autodrift/fresh_ambiguity_measured_mining.py
tests/test_fresh_ambiguity_measured_mining.py
```

It runs a bounded public measured smoke:

```text
runs/m1531_fresh_ambiguity_measured_mining_smoke/summary.json
```

No candidate materialization, corpus export, training, PPO, promotion, private
holdout, actor-input change, or self-identification claim is made.

## Commands

Focused tests:

```bash
PYTHONPATH=src python -m pytest tests/test_fresh_ambiguity_measured_mining.py -q
```

Result:

```text
5 passed
```

Measured smoke:

```bash
PYTHONPATH=src python -m autodrift.fresh_ambiguity_measured_mining --output-dir runs/m1531_fresh_ambiguity_measured_mining_smoke --seed 1531
```

Result:

```text
trace_row_count=1226
measured_pair_candidate_count=10
passes_public_smoke_gates=True
```

## Result Summary

```text
source_row_count: 14
attempted_source_families: 14
reached_reveal_source_families: 14
reached_decision_source_families: 13
trace_row_count: 1226
snapshot_row_count: 68
measured_pair_candidate_count: 10
accepted_measured_pair_count: 3
intervention_row_count: 10
target_replay_failure_count: 1
donor_replay_failure_count: 0
failure_type_counts: did_not_reach_decision_step=1, none=13
max_single_source_family_share: 0.07142857142857142
closed_t5_subset_rows: 0
max_closed_t5_subset_share: 0.0
proxy_fault_family_count: 7
history_interventions_executed: false
passes_public_smoke_gates: true
passes_evidence_quality_targets: false
```

The three accepted measured pairs show that the measured miner can find
same-task, source-diverse pair candidates under the initial relaxed thresholds.
They are not yet self-ID evidence because wrong-history and donor response/action
continuations were not executed in M1531.

## Artifacts

```text
measured_source_spec_rows.csv
measured_trace_rows.csv
measured_snapshot_rows.csv
measured_pair_candidates.csv
measured_intervention_rows.csv
measured_rejected_pairs.csv
measured_source_family_summary.csv
measured_guardrail_summary.csv
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

M1531 is a measured-mining plumbing pass with useful source diversity:

```text
public smoke gates pass;
measured pair candidates exist;
accepted measured pairs exist;
guardrails are clean.
```

But it is not a candidate-export or self-ID pass:

```text
history_interventions_executed: false;
passes_evidence_quality_targets: false;
candidate materialization remains blocked.
```

The next step must audit the measured smoke and decide whether to implement
wrong-history/donor-response continuations or repair the measured-pair criteria.

## Next

```text
m1532-paper-route-fresh-ambiguity-measured-mining-result-audit
```
