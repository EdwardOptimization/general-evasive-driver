# M1419 Paper-Route Warmup Gate Invasiveness Retune Source Smoke

## Summary

M1419 ran the no-training source smoke admitted by M1418. It preserved M1417
obstacle sampling and retuned only the staged warmup gate geometry.

Decision:

```text
warmup_gate_invasiveness_retune_invasiveness_pass_marginal_source_diversity_fail_route_to_synthesis
```

M1419 does not run outcome interventions, train, run PPO, promote, use private
holdout, export a training corpus, or change actor inputs.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.warmup_latched_config_smoke \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m1419_warmup_gate_invasiveness_retune_source_wave.json \
  --seed-start 141900 \
  --seed-count 48 \
  --reveal-steps 48,56,64,72 \
  --history-length 56 \
  --min-warmup-evidence-steps 16 \
  --max-source-rows 6144 \
  --device cpu \
  --run-dir runs/m1419_warmup_gate_invasiveness_retune_source_smoke
```

## Result

```text
result_class: warmup_latched_structural_pass
source_rows: 1714
matched_current_rows: 132
bucketed_current_rows: 158
matched_or_bucketed_reveal_rows: 252
finite_metric_rows: 1714
rejected_rows: 4814
actor_parameters_changed: false
```

Source diversity:

```text
unique_source_seeds: 34
unique_capability_pairs: 16
unique_preferred_fault_families: 9
unique_wrong_fault_families: 9
unique_reveal_buckets: 492
max_single_seed_share: 0.068845
max_single_capability_pair_share: 0.097433
```

Matched/bucketed diversity:

```text
unique_source_seeds: 27
unique_capability_pairs: 16
unique_preferred_fault_families: 9
unique_wrong_fault_families: 9
unique_reveal_buckets: 101
max_single_seed_share: 0.126984
max_single_capability_pair_share: 0.095238
```

## Gate Check

Source and diversity gates:

```text
source_rows >= 1024: pass  # 1714
matched_or_bucketed_reveal_rows >= 240: pass  # 252
matched/bucketed unique_source_seeds >= 28: fail  # 27
matched/bucketed unique_capability_pairs >= 12: pass  # 16
matched/bucketed unique_reveal_buckets >= 64: pass  # 101
finite_metric_rows == source_rows: pass
actor_parameters_changed == false: pass
```

Warmup evidence gates:

```text
warmup_gate_visible_rows: 252 / 252
warmup_evidence_rows: 252 / 252
warmup_response_history_l2_p95: 0.050344  # pass >= 0.035
warmup_action_history_l2_p95: 0.019332  # pass >= 0.008
```

Invasiveness gates:

```text
warmup_gate_collision_share: 0.293651  # pass <= 0.50
clear rows: 174
clear_low_margin rows: 4
clear + clear_low_margin rows: 178  # pass >= 120
collision rows: 74
```

## Interpretation

The retune achieved the intended reduction in warmup-gate pressure:

```text
M1417 matched/bucketed collision share: 0.544000
M1419 matched/bucketed collision share: 0.293651

M1417 clear + clear_low rows: 114
M1419 clear + clear_low rows: 178
```

It also preserved source volume, current matching, capability-pair coverage, and
warmup command-response evidence.

However, it missed the pre-registered matched/bucketed source-seed diversity
threshold by one seed:

```text
required matched/bucketed unique_source_seeds: >= 28
observed matched/bucketed unique_source_seeds: 27
```

This is a marginal source-diversity failure, not a warmup evidence failure and
not an invasiveness failure. It should not be converted directly into outcome
probing without synthesis, because M1419 is also the tenth non-synthesis
milestone after the M1409 branch synthesis.

## Decision

Route to branch synthesis:

```text
m1420-paper-route-warmup-reveal-pressure-retune-branch-synthesis
```

M1420 should decide whether the branch evidence justifies a no-training outcome
probe from the M1419 source despite the one-seed diversity miss, or whether the
branch should stop or pivot.

No further local retune should run before synthesis.

## Guardrails

M1419 does not claim self-identification. It only shows that a less invasive
warmup-gate geometry can preserve source materialization and warmup
command-response evidence while reducing warmup collision pressure.

The next step must not:

```text
train
run PPO
run outcome interventions before synthesis
promote
use private holdout
export a corpus
change actor inputs
claim recurrent-belief advantage
claim level3 self-identification
```
