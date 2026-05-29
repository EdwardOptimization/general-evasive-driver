# M1576 Paper-Route History-Sensitive Active-Set Miner Implementation

## Summary

M1576 implemented and ran the bounded public history-sensitive active-set miner
designed in M1575.

Decision:

```text
history_sensitive_active_set_miner_smoke_partial_pass_high_speed_late_null_route_to_audit
```

The implementation worked and wrote the required public artifacts. It found a
larger clean history-sensitive active set than M1573:

```text
history_sensitive_anchor_count: 32
clean_history_sensitive_anchor_count: 30
clean_history_sensitive_pair_count: 40
```

But it did not pass the public smoke gate because high-speed and late-reveal
history-sensitive anchors remained null:

```text
high_speed_history_sensitive_count: 0
late_reveal_history_sensitive_count: 0
null_result_classification: high_speed_late_null
```

The next step is audit, not threshold tuning, materialization, or training.

## Commands

```bash
PYTHONPATH=src python -m pytest tests/test_history_sensitive_active_set_miner.py -q
```

Result:

```text
3 passed
```

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
  python -m autodrift.history_sensitive_active_set_miner \
  --output-dir runs/m1576_history_sensitive_active_set_miner_smoke \
  --seed 1861 \
  --seed-count 6 \
  --max-source-specs 480 \
  --max-anchor-candidates 512 \
  --max-anchors 256 \
  --continuation-steps 64
```

## Implementation

New code:

```text
src/autodrift/history_sensitive_active_set_miner.py
tests/test_history_sensitive_active_set_miner.py
```

The miner reuses the fixed P0 public actor and existing intervention mechanics:

```text
targeted source generation;
anchor replay;
normal continuation;
source-diverse donor pairing;
wrong-history and donor-plus-hidden interventions;
current-frame substitution controls;
history-vs-control acceptance classifier.
```

No actor input changed.

## Artifacts

```text
runs/m1576_history_sensitive_active_set_miner_smoke/source_spec_rows.csv
runs/m1576_history_sensitive_active_set_miner_smoke/anchor_candidate_rows.csv
runs/m1576_history_sensitive_active_set_miner_smoke/target_anchor_rows.csv
runs/m1576_history_sensitive_active_set_miner_smoke/donor_pair_rows.csv
runs/m1576_history_sensitive_active_set_miner_smoke/history_intervention_rows.csv
runs/m1576_history_sensitive_active_set_miner_smoke/history_sensitive_anchor_rows.csv
runs/m1576_history_sensitive_active_set_miner_smoke/history_sensitive_source_family_summary.csv
runs/m1576_history_sensitive_active_set_miner_smoke/history_sensitive_window_summary.csv
runs/m1576_history_sensitive_active_set_miner_smoke/history_intervention_variant_summary.csv
runs/m1576_history_sensitive_active_set_miner_smoke/control_substitution_summary.csv
runs/m1576_history_sensitive_active_set_miner_smoke/guardrail_summary.csv
runs/m1576_history_sensitive_active_set_miner_smoke/summary.json
```

## Summary Metrics

```text
source_spec_count: 360
anchor_candidate_count: 512
replay_ok_anchor_count: 407
target_anchor_count: 256
donor_pair_count: 512
intervention_row_count: 5632
history_positive_pair_count: 44
clean_history_sensitive_pair_count: 40
history_sensitive_anchor_count: 32
clean_history_sensitive_anchor_count: 30
history_sensitive_source_family_count: 2
history_sensitive_window_count: 5
non_near_family_history_sensitive_count: 11
high_speed_history_sensitive_count: 0
late_reveal_history_sensitive_count: 0
max_single_history_sensitive_family_share: 0.65
control_substitution_dominated_share: 0.083984375
max_primary_history_gap: 0.27718254452797986
max_control_gap: 0.31220594475079233
max_hidden_specific_gap: 0.22036055188987191
guardrail_violation_count: 0
passes_public_smoke_gates: false
passes_evidence_quality_targets: false
```

Classification counts:

```text
control_substitution_dominated: 39
history_null: 429
history_sensitive_clean: 40
history_sensitive_control_overlap: 4
```

## Source-Family Result

```text
t5_boundary_axis_retarget:
  clean_history_sensitive_pair_count: 14
  clean_history_sensitive_anchor_count: 11
  max_primary_history_gap: 0.27718254452797986

t5_near_boundary_warmup:
  clean_history_sensitive_pair_count: 26
  clean_history_sensitive_anchor_count: 19
  max_primary_history_gap: 0.13233165969655536

t5_high_speed_close_obstacle:
  clean_history_sensitive_pair_count: 0
  clean_history_sensitive_anchor_count: 0
  max_primary_history_gap: 0.006224602548898783

late_reveal_boundary:
  clean_history_sensitive_pair_count: 0
  clean_history_sensitive_anchor_count: 0
  max_primary_history_gap: 0.009707924566951132

curved_boundary_obstacle:
  clean_history_sensitive_pair_count: 0
  clean_history_sensitive_anchor_count: 0
  max_primary_history_gap: 0.008609975555096128
```

The clean positives are source-diverse relative to M1573 because they now include
`t5_boundary_axis_retarget`, but they are still not source-diverse enough for the
pre-registered paper route. In particular, the high-speed third source is still
history-null.

## Window Result

Clean positives appeared across five windows:

```text
decision: 6 clean anchors
decision_minus_16: 5 clean anchors
decision_minus_24: 8 clean anchors
reveal: 7 clean anchors
reveal_plus_4: 4 clean anchors
```

This is useful: the miner is not just finding one temporal row. The blocker is
source family, not temporal window coverage.

## Interpretation

Supported:

```text
the M1576 miner implementation is live;
history-sensitive active-set selection is stronger than M1573 flip-anchor-only selection;
clean history-sensitive anchors exist across multiple windows;
control-substitution domination is low overall;
the positive families are t5_near_boundary_warmup and t5_boundary_axis_retarget.
```

Unsupported:

```text
high-speed history sensitivity;
late-reveal history sensitivity;
curved-source history sensitivity;
source-diverse paper-level history necessity;
candidate materialization;
training corpus export;
PPO continuation;
checkpoint promotion;
private-holdout evidence;
level3 anticipatory self-identification.
```

## Failure Taxonomy

```text
scenario_sampling_failure
```

This is not an implementation failure. The harness found many clean positives,
but the positive set does not include the high-speed or late-reveal source
families that the public gate requires.

## Route Decision

Do not route directly to:

```text
candidate materialization;
training corpus export;
PPO;
promotion;
private holdout;
threshold relaxation.
```

Route to:

```text
m1577-paper-route-history-sensitive-active-set-miner-result-audit
```

The audit should decide whether to:

```text
1. design one high-speed/late-reveal history-sensitivity source repair;
2. synthesize the branch because high-speed/late history sensitivity remains null;
3. keep M1576 as public diagnostic evidence only.
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
```

## Next

```text
m1577-paper-route-history-sensitive-active-set-miner-result-audit
```
