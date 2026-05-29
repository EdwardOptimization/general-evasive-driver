# M1582 Paper-Route History Pairability Source-Miner Implementation

## Summary

M1582 implements and runs the pairability-first source miner designed in M1581.

Decision:

```text
history_pairability_source_miner_smoke_public_pass_route_to_audit
```

The result is a clean positive for the prerequisite question:

```text
can the current public P0 source generator produce matched-current
hidden-divergent pairs before history interventions?
```

Yes. The smoke produces a broad source-diverse pairability set and passes both
the public smoke gates and the evidence-quality targets. This is not a
history-necessity result and it is not a training corpus. It only removes the
M1579 pairability bottleneck and routes to audit before any intervention design.

## Implementation

New module:

```text
src/autodrift/history_pairability_source_miner.py
```

Focused tests:

```text
tests/test_history_pairability_source_miner.py
```

Focused test result:

```text
PYTHONPATH=src python -m pytest tests/test_history_pairability_source_miner.py -q
4 passed
```

The miner:

```text
builds source-family balanced public P0 retarget specs;
replays anchors at reveal / post-reveal / pre-decision windows;
captures response/action, context, and recurrent hidden state at the anchor;
screens only cross-source matched-current / hidden-divergent pairs;
writes tiered threshold sweeps and source-edge/window summaries;
does not run history interventions;
does not train, run PPO, export a training corpus, or promote.
```

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.history_pairability_source_miner --output-dir runs/m1582_history_pairability_source_miner_smoke --seed 1901 --seed-count 6 --max-source-specs 480 --max-anchor-candidates 640 --max-pairs 20000
```

## Result

Artifact:

```text
runs/m1582_history_pairability_source_miner_smoke/summary.json
```

Key metrics:

```text
source_spec_count: 480
anchor_candidate_count: 640
replay_ok_anchor_count: 509
pair_screen_candidate_count: 20000
tier_a_pair_count: 20000
tier_b_pair_count: 20000
tier_c_pair_count: 20000
pairable_source_edge_count: 24
pairable_target_source_family_count: 8
pairable_window_count: 6
high_speed_or_late_pair_count: 108
max_single_pairable_source_edge_share: 0.0742
passes_public_smoke_gates: true
passes_evidence_quality_targets: true
null_result_classification: pairability_public_pass
```

The top capped pairability set is not source-singleton. The largest source-edge
share is `0.0742`, and the pairable set spans `24` source edges, `8` endpoint
source families, and `6` anchor windows.

High-speed or late-reveal sources are present but still smaller than the broad
pairable set:

```text
high_speed_or_late_pair_count: 108
late_reveal_boundary endpoint pairs: 108
```

This is enough for the M1581 public gate, but M1583 should audit whether the
high-speed/late subset is sufficiently diverse for the next intervention design
or should be treated as a diagnostic subset.

## Guardrails

```text
history_interventions_executed: false
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

## Supported Claims

M1582 supports:

```text
the M1579 matched-pair shortfall was not a fundamental P0 replay limitation;
broad public P0 source generation can produce many matched-current hidden-divergent pairs;
source-edge concentration is low in the capped pairability set;
the pairability prerequisite for a new wrong-history intervention design is satisfied.
```

## Unsupported Claims

M1582 does not support:

```text
history necessity;
source-diverse self-identification;
high-speed or late-reveal history sensitivity;
candidate materialization;
training corpus export;
PPO continuation;
checkpoint promotion;
private holdout evidence;
paper-level result;
level3 anticipatory self-identification.
```

## Route Decision

Do not route directly to interventions, materialization, training, PPO, or
promotion. The next step is an audit:

```text
m1583-paper-route-history-pairability-source-miner-result-audit
```

The audit should decide whether to design a bounded source-diverse
wrong-history intervention over the pairable set, and should explicitly handle
the capped-top-pair interpretation and the smaller high-speed/late subset.
