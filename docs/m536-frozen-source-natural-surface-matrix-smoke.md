# M536 Frozen Source Natural-Surface Matrix Smoke

## Purpose

M536 scales the M535 evaluator from a 3-checkpoint / 2-pair smoke to the full
nine-checkpoint L0/L2/L3 matrix on small public natural-surface subsets.

This is still a smoke. It does not promote a checkpoint and does not establish a
stable baseline ranking.

## Commands

Short-reveal subset:

```bash
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m autodrift.frozen_source_surface_eval \
  --source-checkpoint runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --baseline-checkpoint l0_s3530=L0_current_observation:runs/m532_matched_l0_short_train_seed3530/checkpoint.pt \
  --baseline-checkpoint l2_s3530=L2_finite_window:runs/m532_matched_l2_short_train_seed3530/checkpoint.pt \
  --baseline-checkpoint l3_s3530=L3_online_gru:runs/m532_matched_l3_short_train_seed3530/checkpoint.pt \
  --baseline-checkpoint l0_s3531=L0_current_observation:runs/m533_matched_l0_short_train_seed3531/checkpoint.pt \
  --baseline-checkpoint l2_s3531=L2_finite_window:runs/m533_matched_l2_short_train_seed3531/checkpoint.pt \
  --baseline-checkpoint l3_s3531=L3_online_gru:runs/m533_matched_l3_short_train_seed3531/checkpoint.pt \
  --baseline-checkpoint l0_s3532=L0_current_observation:runs/m533_matched_l0_short_train_seed3532/checkpoint.pt \
  --baseline-checkpoint l2_s3532=L2_finite_window:runs/m533_matched_l2_short_train_seed3532/checkpoint.pt \
  --baseline-checkpoint l3_s3532=L3_online_gru:runs/m533_matched_l3_short_train_seed3532/checkpoint.pt \
  --env-config configs/m494_natural_belief_short_reveal_zero_relvel.json \
  --pairs-csv runs/m497_natural_belief_decision_window_outcome_gate/targeted_pairs_short_reveal.csv \
  --tail-offsets 0,2 \
  --max-continuation-steps 40 \
  --max-pairs 8 \
  --device cpu \
  --run-dir runs/m536_frozen_source_matrix_smoke_short_reveal
```

Warmup-capability subset used the same checkpoint matrix with:

```text
env-config = configs/m494_natural_belief_warmup_capability_zero_relvel.json
pairs-csv = runs/m497_natural_belief_decision_window_outcome_gate/targeted_pairs_warmup_capability.csv
run-dir = runs/m536_frozen_source_matrix_smoke_warmup_capability
```

## Route Results

```text
short_reveal:
  input_pair_count = 8
  source_snapshot_count = 15
  outcome_row_count = 135
  invalid_row_count = 1
  invalid = pair_id 3, left_seed 12003, left_tail_step 38, tail_offset 2

warmup_capability:
  input_pair_count = 8
  source_snapshot_count = 10
  outcome_row_count = 144
  invalid_row_count = 0
```

The one short-reveal invalid row is diagnosed as `missing_source_tail_snapshot`.
It is a small source-tail availability issue, not a metadata or actor-contract
failure.

## Aggregate Smoke Metrics

Across both small subsets:

| Level | Rows | Success Rate | Obstacle Completion Rate | Collision Rate | Return Mean | Margin Mean |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| L0 current observation | `93` | `0.967742` | `0.516129` | `0.032258` | `33.928705` | `1.754461` |
| L2 finite window | `93` | `0.967742` | `0.516129` | `0.032258` | `34.283690` | `1.757335` |
| L3 online GRU | `93` | `0.967742` | `0.516129` | `0.032258` | `33.943047` | `1.884178` |

On this tiny matrix smoke, all levels tie on success/completion/collision;
L3 has the best clearance margin mean. This is route evidence only.

## Interpretation

M536 passes the matrix smoke gate. The evaluator scales to all nine matched
short-train checkpoints and both M497 natural surface splits.

The next step should run the full public natural diagnostic, including:

```text
M497 short_reveal: offsets 0,2,4,8
M497 warmup_capability: offsets 0,2,4,8
M487 near_threshold: offsets 4,8,12,16
M487 late_high_energy: offsets 4,8,12,16
```

M526 event rows should remain a public diagnostic overlay, not a private
holdout.

## Decision

```text
matrix_smoke_pass_admit_m537_full_public_natural_eval
```
