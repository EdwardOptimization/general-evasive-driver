# M13 Near-Threshold Paired Gate

Last updated: 2026-05-21

## Purpose

M12 proved that paired hidden-friction perturbation infrastructure works, but
the sampled scenarios were still too label dominated. M13 strengthens the gate
by first building a near-threshold seed corpus. The corpus keeps only seeds
where the obstacle lateral feasibility margin is close to the AES/drift
boundary and the friction perturbation happens before the obstacle is reached.

## Implementation

New CLI:

```bash
python -m autodrift.near_threshold_corpus
```

The selected CSV includes:

- seed;
- obstacle label;
- normalized threshold score;
- AES and drift lateral margins;
- friction-step timing;
- hidden vehicle-road buckets for diagnostics.

`python -m autodrift.paired_perturbation_gate` now also supports `--seed-csv`,
so the paired gate can evaluate a deterministic stress corpus instead of a
contiguous seed range.

## Corpus

Command:

```bash
conda run -n autodrift python -m autodrift.near_threshold_corpus \
  --env-config configs/m11_online_recurrent_history_critical_eval.json \
  --seed-start 3000 \
  --max-candidates 5000 \
  --count 40 \
  --max-threshold-score 0.20 \
  --min-time-after-step 0.10 \
  --label drift_required \
  --label unavoidable \
  --run-dir runs/m13_near_threshold_corpus_seed3000
```

Result:

| metric | value |
| --- | ---: |
| selected seeds | 40 |
| candidates searched | 5000 |
| `drift_required` seeds | 19 |
| `unavoidable` seeds | 21 |
| max threshold score | 0.009 |
| mean threshold score | 0.005 |

## Gate

Command:

```bash
conda run -n autodrift python -m autodrift.paired_perturbation_gate \
  --env-config configs/m11_online_recurrent_history_critical_eval.json \
  --seed-csv runs/m13_near_threshold_corpus_seed3000/scenario_corpus.csv \
  --checkpoint runs/ppo_m11_online_recurrent_driver_seed411/checkpoint.pt \
  --checkpoint-policy m11=runs/ppo_m11_online_recurrent_driver_seed411/checkpoint.pt \
  --checkpoint-policy m11_reset=runs/ppo_m11_online_recurrent_driver_seed411/checkpoint.pt@reset_recurrent_state \
  --checkpoint-policy m11_zero_current=runs/ppo_m11_online_recurrent_driver_seed411/checkpoint.pt@zero_current_response \
  --checkpoint-policy m11_zero_all=runs/ppo_m11_online_recurrent_driver_seed411/checkpoint.pt@zero_all_response \
  --device cpu \
  --run-dir runs/m13_near_threshold_paired_gate_seed3000
```

Paired result:

| policy | nominal success | perturbed success | success drop | return delta |
| --- | ---: | ---: | ---: | ---: |
| M11 | 0.750 | 0.375 | 0.375 | -18.160 |
| M11 reset recurrent state | 0.750 | 0.375 | 0.375 | -17.990 |
| M11 zero current response | 0.750 | 0.375 | 0.375 | -17.975 |
| M11 zero all response | 0.750 | 0.375 | 0.375 | -17.975 |

Pair counts for M11:

| case | count |
| --- | ---: |
| nominal success, perturbed failure | 15 |
| nominal failure, perturbed success | 0 |
| both success | 15 |
| both failure | 10 |

The reset and response-masked variants have the same pair counts.

## Conclusion

M13 is an important gate improvement. Unlike M12, this corpus is actually
behavior-critical: changing hidden post-step friction changes success on 15 of
40 paired seeds.

The policy result is still negative. M11, recurrent-state reset, and
response-masked variants all show the same success drop. The gate now exposes a
real hidden-response stressor, but the current driver does not use recurrent
memory or current response strongly enough to adapt differently.

## Next Step

M14 should train against this type of near-threshold perturbation instead of
only evaluating it. The next training config should emphasize:

- single-frame online recurrent observation;
- friction-step perturbations before obstacle arrival;
- near-threshold `drift_required` and `unavoidable` obstacle cases;
- success and recovery after the perturbation, not only static obstacle pass.

The M14 gate should re-run this exact corpus and require a measurable difference
between normal recurrent inference and `reset_recurrent_state`.
