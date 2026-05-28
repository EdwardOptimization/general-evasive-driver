# M1394 Paper-Route Warmup-Latched Config Smoke

## Summary

M1394 implements and runs a no-training warmup-latched source/config smoke for
the two-phase causal-history route designed in M1393.

Decision:

```text
warmup_latched_config_smoke_structural_pass_admit_outcome_probe
```

This is a structural source smoke only. It does not train, run PPO, promote a
checkpoint, use private holdout data, export a training corpus, or change actor
inputs.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.warmup_latched_config_smoke \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m991_capability_step_fault_source_wave.json \
  --seed-start 139400 \
  --seed-count 32 \
  --reveal-steps 48,56,64,72 \
  --history-length 36 \
  --min-warmup-evidence-steps 8 \
  --max-source-rows 4096 \
  --device cpu \
  --run-dir runs/m1394_warmup_latched_config_smoke
```

## Result

Artifact:

```text
runs/m1394_warmup_latched_config_smoke/summary.json
```

Key counts:

```text
result_class: warmup_latched_structural_pass
source_rows: 2580
matched_current_rows: 270
bucketed_current_rows: 436
matched_or_bucketed_reveal_rows: 604
finite_metric_rows: 2580
rejected_rows: 1772
```

Source diversity:

```text
source unique_source_seeds: 28
source unique_capability_pairs: 16
source unique_reveal_buckets: 393
matched/bucketed unique_source_seeds: 27
matched/bucketed unique_capability_pairs: 16
matched/bucketed unique_reveal_buckets: 131
matched/bucketed max_single_seed_share: 0.0894
matched/bucketed max_single_capability_pair_share: 0.1010
```

Distance diagnostics:

```text
warmup_history_l2_mean: 0.03127
warmup_history_l2_p95: 0.07154
current_hidden_l2_mean: 0.23777
current_hidden_l2_p95: 0.58974
scene_context_l2_mean: 0.03639
obstacle_position_l2_mean: 0.00498
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

## Interpretation

M1394 shows that the repository can materialize warmup/reveal rows where hidden
capability evidence exists before the emergency reveal, while the reveal frame
is either strictly matched or bucketed across capability families. The
structural thresholds from M1393 are met:

```text
source_rows >= 512
matched_or_bucketed_reveal_rows >= 160
unique_source_seeds >= 24
unique_capability_pairs >= 8
unique_reveal_buckets >= 8
finite metrics
```

This does not prove self-identification. It only admits the next no-training
outcome-intervention probe over the matched/bucketed warmup-latched rows.

## Next

M1395 should run or implement a no-training warmup-latched outcome probe over:

```text
runs/m1394_warmup_latched_config_smoke/matched_or_bucketed_rows.csv
```

Required variants:

```text
normal
reset_hidden
zero_current_response
delayed_warmup_history
wrong_warmup_history_same_reveal
same_recent_wrong_warmup_history
warmup_removed_or_shortened
```

Rows should only count as warmup-history positive when the normal rollout is
viable, the reveal matching/bucketing control holds, and a history intervention
causes an outcome-relevant margin or success gap. Reset-only or zero-current-only
effects must remain positive controls, not self-identification evidence.
