# M183 M182 Boundary-Outcome Corpus Objective

M182 produced the first robustness-passing, source-diverse boundary
wrong-history proof surface for the current M168/M170 branch. M183 converts
that surface into deduplicated boundary-outcome corpora and verifies that the
fixed objective is not detached from replayed outcomes.

This milestone is still objective/replay sanity only. It does not run PPO.

## Input Contract

The deployable actor input contract is unchanged:

```text
P0 human-view observation + recurrent hidden state from command-response history
```

The M182 accepted rows, relocated obstacle geometry, target names, group ids,
scores, and labels are training-time artifacts only. They are not actor inputs.

## Corpus Builder

Small cleanup:

```text
src/autodrift/boundary_outcome_corpus_objective.py
```

The artifact `actor_contract` text is now milestone-neutral:

```text
student features are human-view observation and recurrent hidden states
reconstructed from deployable P0 command-response history; relocated outcomes
are labels only
```

## M168 Strict Corpus

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.boundary_outcome_corpus_objective \
  --checkpoint-policy m168_strict=runs/ppo_m168_stage1_from_m167_5168_seed6168/checkpoint.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --boundary-rows-csv runs/m182_boundary_robustness_seed9510/accepted_wrong_history_rows.csv \
  --delay-steps 10 \
  --device cpu \
  --max-rows-per-physical-pair 2 \
  --optimization-seeds 9620,9621,9622 \
  --steps 180 \
  --batch-size 64 \
  --learning-rate 0.0003 \
  --weight-decay 0.001 \
  --hidden-dim 96 \
  --run-dir runs/m183_m168_boundary_outcome_corpus_dedup_seed9510
```

Artifacts:

```text
runs/m183_m168_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.npz
runs/m183_m168_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv
runs/m183_m168_boundary_outcome_corpus_dedup_seed9510/corpus_summary.json
runs/m183_m168_boundary_outcome_corpus_dedup_seed9510/objective_summary.json
```

Corpus:

| Metric | Value |
| --- | ---: |
| rows | 16 |
| physical pairs | 14 |
| targets | 3 |
| unique boundary geometries | 16 |
| max rows / physical pair | 2 |
| max rows / physical pair fraction | 0.125000 |
| success-drop rows | 16 |
| mean margin gap | 0.008047 |
| max margin gap | 0.010628 |
| action reconstruction error max | 0.0 |

Objective sanity:

| Metric | Value |
| --- | ---: |
| objective pass | true |
| seed pass count | 3 / 3 |
| mean val combined loss improvement | 3.257694 |
| min val combined loss improvement | 2.680247 |
| mean val delta loss improvement | 4.105362 |
| min val delta loss improvement | 3.403516 |
| mean val pairwise accuracy after | 1.000000 |
| min val pairwise accuracy after | 1.000000 |

## M170 Split-Aware Corpus

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.boundary_outcome_corpus_objective \
  --checkpoint-policy m170_split=runs/ppo_m170_row67_guarded_stage2_seed7170/checkpoint.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --boundary-rows-csv runs/m182_boundary_robustness_seed9510/accepted_wrong_history_rows.csv \
  --delay-steps 10 \
  --device cpu \
  --max-rows-per-physical-pair 2 \
  --optimization-seeds 9620,9621,9622 \
  --steps 180 \
  --batch-size 64 \
  --learning-rate 0.0003 \
  --weight-decay 0.001 \
  --hidden-dim 96 \
  --run-dir runs/m183_m170_boundary_outcome_corpus_dedup_seed9510
```

Artifacts:

```text
runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.npz
runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv
runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/corpus_summary.json
runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/objective_summary.json
```

Corpus:

| Metric | Value |
| --- | ---: |
| rows | 17 |
| physical pairs | 15 |
| targets | 3 |
| unique boundary geometries | 17 |
| max rows / physical pair | 2 |
| max rows / physical pair fraction | 0.117647 |
| success-drop rows | 17 |
| mean margin gap | 0.007982 |
| max margin gap | 0.010772 |
| action reconstruction error max | 0.0 |

Objective sanity:

| Metric | Value |
| --- | ---: |
| objective pass | true |
| seed pass count | 3 / 3 |
| mean val combined loss improvement | 2.847660 |
| min val combined loss improvement | 2.280107 |
| mean val delta loss improvement | 3.614255 |
| min val delta loss improvement | 2.920117 |
| mean val pairwise accuracy after | 0.952381 |
| min val pairwise accuracy after | 0.857143 |

## Replay Sanity

M183 then verifies that the deduplicated corpus rows still replay as actual
normal-history success and wrong-history failure.

M168 corpus command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.boundary_outcome_replay_gate \
  --checkpoint-policy m168_strict=runs/ppo_m168_stage1_from_m167_5168_seed6168/checkpoint.pt \
  --checkpoint-policy m170_split=runs/ppo_m170_row67_guarded_stage2_seed7170/checkpoint.pt \
  --corpus-csv runs/m183_m168_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --max-continuation-steps 60 \
  --baseline-policy m168_strict \
  --candidate-policy m170_split \
  --max-normal-success-drop 0.0 \
  --max-normal-margin-regression 0.005 \
  --max-margin-gap-regression 0.001 \
  --max-success-drop-count-regression 0 \
  --device cpu \
  --run-dir runs/m183_m168_boundary_replay_sanity_seed9510
```

M170 corpus command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.boundary_outcome_replay_gate \
  --checkpoint-policy m170_split=runs/ppo_m170_row67_guarded_stage2_seed7170/checkpoint.pt \
  --checkpoint-policy m168_strict=runs/ppo_m168_stage1_from_m167_5168_seed6168/checkpoint.pt \
  --corpus-csv runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --max-continuation-steps 60 \
  --baseline-policy m170_split \
  --candidate-policy m168_strict \
  --max-normal-success-drop 0.0 \
  --max-normal-margin-regression 0.005 \
  --max-margin-gap-regression 0.001 \
  --max-success-drop-count-regression 0 \
  --device cpu \
  --run-dir runs/m183_m170_boundary_replay_sanity_seed9510
```

Replay result:

| Corpus | Rows | Baseline normal success | Baseline wrong success | Baseline success drops | Cross-branch success drops | Gate pass |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| M168 strict | 16 | 1.000000 | 0.000000 | 16 | 16 | true |
| M170 split | 17 | 1.000000 | 0.000000 | 17 | 17 | true |

The replay sanity is stronger than M162/M164: every deduplicated M183 row
replays as normal-history success and wrong-history failure under its source
checkpoint, and the opposite branch preserves the same success-drop count.

## Decision

M183 is positive.

Both M168 and M170 corpora are admitted for guarded actor-update design. PPO is
still blocked. The next step is a small M184 actor-coupling update with strong
action anchors, followed by behavior retention, protected-key replay, and M182
boundary replay gates before any PPO continuation.

Preferred next branch:

```text
start from M168 strict first
```

Rationale: M168 remains the strict full-replay anchor, while M170 is
split-aware and previously lost knife-edge row 67.
