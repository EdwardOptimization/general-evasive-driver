# M350 Old-Key Neighborhood PPO Escalation Design

M350 designs the next PPO escalation after M349 promotion. It does not run PPO,
repair, replay, behavior gates, or promotion.

## Rationale

M349 promotes:

```text
runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_01.pt
```

This is the first public-gate base accepted under the distributional old-key
neighborhood gate rather than the stale singleton `9944` gap-floor veto. The
next PPO step should therefore keep the M335 short-PPO recipe conservative, but
replace the old `9944` floor in the acceptance stack with:

```text
M341 compact old-key neighborhood targeted replay
old_key_neighborhood_replay_gate candidate metrics
```

The old singleton key remains a visible diagnostic through the neighborhood
surface; it is not restored as the sole continuation veto.

## Base

Current public-gate base:

```text
runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_01.pt
```

## Registered Config

Config:

```text
configs/ppo_m351_old_key_neighborhood_escalation.json
```

Key PPO settings:

| Field | Value |
| --- | ---: |
| total_steps | 4096 |
| rollout_steps | 128 |
| num_envs | 8 |
| minibatch_size | 512 |
| learning_rate | 5e-7 |
| seed | 5239 |
| checkpoint_interval_steps | 1024 |

The config keeps the same human-view recurrent actor contract and auxiliary
guard structure as M335:

```text
response_prediction_aux_coef = 0.06
outcome_intervention_aux_coef = 0.06
rejected_history_preference_aux_coef = 0.03
baseline_action_anchor_coef = 100.0
snippet_action_anchor_coef = 100.0
trajectory_action_anchor_coef = 100.0
```

The baseline and snippet action anchors are updated to the M349 public base.

## Planned M351 Commands

Raw PPO proposal:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_m351_old_key_neighborhood_escalation.json \
  --init-checkpoint runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_01.pt \
  --run-dir runs/ppo_m351_old_key_neighborhood_escalation_seed5239
```

Exact post-PPO repair:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.exact_post_ppo_repair \
  --base-checkpoint runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_01.pt \
  --raw-checkpoint runs/ppo_m351_old_key_neighborhood_escalation_seed5239/checkpoint.pt \
  --preference-npz runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz \
  --outcome-npz runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz \
  --device cpu \
  --start-mode repair_from_raw \
  --steps 40 \
  --seed 10101 \
  --run-dir runs/m351_exact_repair_from_raw_s40_seed10101
```

If the repaired endpoint passes exact objectives but fails old-key neighborhood
acceptance, M351 should run an interpolation from M349 base to the repaired
endpoint:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.checkpoint_interpolation \
  --base-checkpoint runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_01.pt \
  --target-checkpoint runs/m351_exact_repair_from_raw_s40_seed10101/candidate_checkpoint.pt \
  --alphas 0 0.0025 0.005 0.0075 0.01 0.02 0.05 0.1 0.2 0.4 0.6 0.8 1.0 \
  --label-prefix m351_a \
  --run-dir runs/m351_m349_to_repaired_old_key_neighborhood_interpolation
```

Old-key neighborhood targeted replay should be run for the repaired endpoint or
for each interpolation candidate:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.old_key_neighborhood_targeted_replay \
  --reference-manifest runs/m341_old_key_neighborhood_block_a_seed9860/manifest.json \
  --compact-corpus-csv runs/m341_old_key_neighborhood_mining/old_key_neighborhood_compact_corpus.csv \
  --checkpoint-policy m349_base=runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_01.pt \
  --checkpoint-policy m351_candidate=<candidate_checkpoint> \
  --device cpu \
  --run-dir <candidate_old_key_replay_run_dir>
```

Then convert the targeted replay output into a pass/fail decision:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.old_key_neighborhood_replay_gate \
  --compact-corpus-csv runs/m341_old_key_neighborhood_mining/old_key_neighborhood_compact_corpus.csv \
  --guard-results-csv <candidate_old_key_replay_run_dir>/guard_results.csv \
  --baseline-policy m349_base \
  --candidate-policy m351_candidate \
  --run-dir <candidate_old_key_gate_run_dir>
```

## Gate Order

M351 must use this order:

1. Run raw PPO as proposal only.
2. Run exact M297/M270 repair from raw.
3. Reject immediately if exact M297 or M270 regress versus M349.
4. Run source-diverse protected gates.
5. Run old-key neighborhood targeted replay and replay-gate adapter.
6. If needed, run bounded interpolation from M349 to repaired candidate and
   re-evaluate exact/source-diverse/old-key neighborhood gates on selected
   alphas.
7. Run M183/M170 and M267/M264 first replay gates.
8. Admit a separate full public gate only if all proof gates pass.

M351 must not promote directly. A passing M351 should admit M352 full public
gate.

## Decision

Admit:

```text
m351-old-key-neighborhood-ppo-escalation-run
```

Decision:

```text
admit_m351_old_key_neighborhood_ppo_escalation_run
```
