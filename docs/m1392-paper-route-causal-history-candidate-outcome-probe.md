# M1392 Paper-Route Causal History Candidate Outcome Probe

## Summary

M1392 implements and runs a no-training outcome-intervention probe over M1391
matched-current candidates.

Decision:

```text
causal_history_candidate_outcome_history_sparse_route_to_warmup_latched_task_design
```

M1392 performs no training, PPO, promotion, private holdout, actor-input
expansion, or training-corpus export.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.causal_history_candidate_outcome_probe \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m991_capability_step_fault_source_wave.json \
  --candidate-rows runs/m1391_causal_history_source_miner/candidate_rows.csv \
  --max-candidate-rows 384 \
  --per-fault-pair-cap 48 \
  --history-length 12 \
  --recent-window-length 2 \
  --max-continuation-steps 48 \
  --device cpu \
  --run-dir runs/m1392_causal_history_candidate_outcome_probe
```

Artifacts:

```text
runs/m1392_causal_history_candidate_outcome_probe/summary.json
runs/m1392_causal_history_candidate_outcome_probe/outcome_rows.csv
runs/m1392_causal_history_candidate_outcome_probe/accepted_outcome_rows.csv
runs/m1392_causal_history_candidate_outcome_probe/accepted_self_id_rows.csv
runs/m1392_causal_history_candidate_outcome_probe/variant_summary.csv
```

## Result

Run class:

```text
result_class: causal_history_outcome_history_sparse
```

Core counts:

```text
selected_candidate_rows: 384
outcome_rows: 2688
accepted_outcome_rows: 633
accepted_self_id_rows: 24
accepted_reset_rows: 363
accepted_zero_current_rows: 246
action_critical_rows: 1304
normal_failed_rows: 0
rejected_rows: 0
variant_count: 7
```

Guardrails:

```text
actor_parameters_changed: false
training_started: false
evaluation_started: false
ppo_used: false
promoted: false
private_holdout_used: false
training_corpus_exported: false
actor_input_contract_changed: false
```

## Variant Summary

| Variant | Rows | Outcome Critical | Self-ID Relevant | Margin Gap Mean | Sequence Action L2 Mean |
| --- | ---: | ---: | ---: | ---: | ---: |
| `delayed_history_4` | 384 | 0 | 0 | 0.00019 | 0.01369 |
| `delayed_history_8` | 384 | 5 | 5 | 0.00069 | 0.02840 |
| `delayed_history_12` | 384 | 19 | 19 | 0.00191 | 0.04668 |
| `wrong_same_current_history` | 384 | 0 | 0 | 0.00003 | 0.00190 |
| `same_recent_wrong_older_history` | 384 | 0 | 0 | 0.00003 | 0.00177 |
| `reset_hidden` | 384 | 363 | 0 | 0.03891 | 0.90506 |
| `zero_current_response` | 384 | 246 | 0 | 0.03894 | 0.42477 |

No variant produced a success drop. The accepted rows are margin/action rows.

## Source Diversity

Accepted outcome diversity:

```text
rows: 633
unique_source_seeds: 38
unique_fault_pairs: 8
unique_variants: 4
max_single_seed_share: 0.11690
max_single_fault_pair_share: 0.14692
```

Accepted self-ID relevant diversity:

```text
rows: 24
unique_source_seeds: 1
unique_fault_pairs: 8
unique_variants: 2
max_single_seed_share: 1.0
max_single_fault_pair_share: 0.20833
```

The broad outcome signal is real, but it is mostly reset/zero-current. The
self-ID relevant signal is delayed-history only and seed-narrow.

## Interpretation

Supported:

```text
1. The candidate outcome probe is implemented and runnable.
2. M1391 candidates are normal-viable in this probe (`normal_failed_rows=0`).
3. Current-frame and recurrent-state controls have strong outcome effects:
   reset_hidden and zero_current_response produce many outcome-critical rows.
4. Delayed history has a small margin/action signal.
```

Not supported:

```text
1. source-diverse history-causal outcome evidence;
2. wrong same-current history sensitivity;
3. same-recent wrong-older-history sensitivity;
4. success-drop or collision event evidence;
5. training corpus export;
6. level3 self-identification.
```

## Failure Taxonomy

Classification:

```text
source_narrow_history_signal
```

Reason:

```text
accepted_self_id_rows=24, but accepted_self_id_unique_seeds=1.
```

Secondary classification:

```text
current_feedback_only_signal risk
```

Reason:

```text
reset_hidden and zero_current_response dominate the accepted outcome rows,
while wrong_same_current_history and same_recent_wrong_older_history have zero
accepted rows.
```

This is not a code failure. It is useful negative evidence about the current
M1375/M1391 source family.

## Next Route

Do not export a corpus and do not train.

Route to:

```text
m1393-paper-route-warmup-latched-causal-history-task-design
```

The next task should design a source distribution where useful history is not a
late reset artifact and not confined to one seed. The task should make
pre-emergency warmup response informative, then reveal an emergency with matched
or bucketed current frame so current-frame substitution is weaker.

## Decision

```text
causal_history_candidate_outcome_history_sparse_route_to_warmup_latched_task_design
```

Next:

```text
m1393-paper-route-warmup-latched-causal-history-task-design
```
