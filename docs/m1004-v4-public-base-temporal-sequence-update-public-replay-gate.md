# M1004 V4 Public Base Temporal Sequence Update Public Replay Gate

## Purpose

M1004 implements and runs the no-training public replay/proof gate designed in
M1003 for M1002 temporal sequence objective candidates.

This milestone does not run PPO, use private holdout, or promote a checkpoint.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.capability_step_temporal_sequence_public_replay_gate \
  --base-checkpoint runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt \
  --candidate-checkpoints runs/m1002_v4_public_base_temporal_sequence_objective_update_probe/candidate_checkpoints.csv \
  --interpolation-metrics runs/m1002_v4_public_base_temporal_sequence_objective_update_probe/interpolation_metrics.csv \
  --corpus runs/m997_v4_public_base_temporal_sequence_corpus_export/temporal_sequence_corpus.npz \
  --base-summary runs/m1000_v4_public_base_temporal_sequence_objective_evaluator/summary.json \
  --run-dir runs/m1004_v4_public_base_temporal_sequence_update_public_replay_gate \
  --device auto \
  --behavior-episodes 80 \
  --max-continuation-steps 60
```

## Result

```text
result_class: temporal_sequence_public_replay_gate_no_preflight_candidate
failure_types: proof_washout
exact_contract_pass_count: 5 / 5
candidate_preflight_pass_count: 0 / 5
selected_alpha: none
ppo_used: false
promoted: false
```

The exact/contract tier reproduced M1002: all five candidates remained exact
temporal objective candidates, actor inputs were unchanged, and only
`actor_mean` differed from the M974 base.

## Exact Tier

| alpha | exact gate | contract gate | weighted total | temporal pref | logp gap | action L2 mean / max |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| 0.20 | pass | pass | -0.907863 | 0.463279 | 0.758060 | 0.008939 / 0.036729 |
| 0.10 | pass | pass | -0.895237 | 0.477309 | 0.697890 | 0.004487 / 0.018600 |
| 0.05 | pass | pass | -0.888472 | 0.484425 | 0.668700 | 0.002248 / 0.009359 |
| 0.02 | pass | pass | -0.884271 | 0.488724 | 0.651472 | 0.000900 / 0.003758 |
| 0.01 | pass | pass | -0.882848 | 0.490161 | 0.645777 | 0.000450 / 0.001881 |

## M267/M264 Preflight

All candidates failed the preflight because success-drop retention regressed.

| alpha | base drops | candidate drops | lost drops | normal margin delta | margin gap delta |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0.20 | 17 | 6 | 11 | +0.003522 | +0.000625 |
| 0.10 | 17 | 11 | 6 | +0.001767 | +0.000308 |
| 0.05 | 17 | 13 | 4 | +0.000885 | +0.000154 |
| 0.02 | 17 | 15 | 2 | +0.000355 | +0.000061 |
| 0.01 | 17 | 15 | 2 | +0.000177 | +0.000031 |

Even the smallest exact candidate made rows `6` and `15` wrong-history
successful:

```text
row 6:
  base normal/wrong margins:      0.011315 / -0.000117
  alpha 0.01 normal/wrong margins: 0.011511 /  0.000033

row 15:
  base normal/wrong margins:      0.006403 / -0.000025
  alpha 0.01 normal/wrong margins: 0.006630 /  0.000171
```

Normal success was retained for every alpha. The failure is that the temporal
actor_mean update made the wrong-history branch safer on near-zero proof rows.
This is a proof-washout failure, not broad behavior regression and not a
contract violation.

## Full Replay And Behavior

Full six-surface replay and behavior seeds were intentionally not run because
the pre-registered M267/M264 preflight had no passing candidate.

## Artifacts

```text
runs/m1004_v4_public_base_temporal_sequence_update_public_replay_gate/summary.json
runs/m1004_v4_public_base_temporal_sequence_update_public_replay_gate/exact_contract_summary.csv
runs/m1004_v4_public_base_temporal_sequence_update_public_replay_gate/candidate_preflight_summary.csv
```

## Decision

```text
temporal_sequence_public_replay_gate_no_preflight_candidate_route_to_replay_failure_audit
```

Next:

```text
m1005-v4-public-base-temporal-sequence-update-replay-failure-audit
```
