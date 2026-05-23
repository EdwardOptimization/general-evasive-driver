# M384 Old-Key Local-Recovery Target Export

M384 exports real replay-selected local recovery targets for the cumulative
old-key gap-tail rows. This milestone does not run PPO, does not promote a
checkpoint, and does not change the deployable actor contract.

## Source

Current public-gate base:

```text
runs/m378_v2_gap_tail_final_interpolation/checkpoints/alpha_0_05.pt
```

Source rows:

```text
runs/m380_alpha01_cumulative_old_key_boundary_audit/gap_tail_rows.csv
```

Reference reconstruction manifest:

```text
runs/m341_old_key_neighborhood_block_a_seed9860/manifest.json
```

## Exporter

M384 adds:

```text
src/autodrift/old_key_recovery_targets.py
tests/test_old_key_recovery_targets.py
```

The exporter reconstructs old-key snapshots, relocates the obstacle to the
gap-tail geometry, evaluates a one-step local action grid around the current
base action, and then rolls out the remainder of the episode under the same
policy. Recovery targets are accepted only when the one-step action improves
normal-history terminal clearance margin by the preregistered threshold.

The exported corpus keeps only deployable actor-facing tensors:

```text
observation
preferred_hidden
rejected_hidden
recovery_action
rejected_anchor_action
weight
row_id
```

The simulator is used only to choose training-time targets.

## Search

Command family:

```text
PYTHONPATH=src python -m autodrift.old_key_recovery_targets \
  --checkpoint runs/m378_v2_gap_tail_final_interpolation/checkpoints/alpha_0_05.pt \
  --reference-manifest runs/m341_old_key_neighborhood_block_a_seed9860/manifest.json \
  --source-rows-csv runs/m380_alpha01_cumulative_old_key_boundary_audit/gap_tail_rows.csv \
  --steer-deltas=-0.06,-0.04,-0.02,-0.01,0,0.01,0.02,0.04,0.06 \
  --throttle-deltas=-0.04,-0.02,0,0.02 \
  --brake-deltas=-0.06,-0.04,-0.02,0,0.02,0.04,0.06 \
  --min-margin-improvement 1e-5 \
  --max-action-l2 0.09 \
  --max-continuation-steps 40 \
  --include-base-retention \
  --device cpu \
  --run-dir runs/m384_old_key_local_recovery_targets
```

Result:

```text
rows_requested: 4
candidate_rollouts: 1008
recovery_rows: 4
accepted_recovery_rows: 4
base_retention_rows: 0
skipped_rows: 0
accepted_margin_improvement_min: 0.003760697
accepted_margin_improvement_mean: 0.005159597
accepted_margin_improvement_max: 0.006008820
candidate_margin_improvement_max: 0.006553879
```

Each row found many accepted local actions:

```text
row 0 accepted candidates: 136
row 1 accepted candidates: 132
row 2 accepted candidates: 137
row 3 accepted candidates: 137
```

The selected actions consistently reduce steer by `0.06`, reduce throttle by
`0.04`, and reduce brake magnitude by `0.04` in this local grid. They are
therefore real replay-selected recovery targets, not copied preferred actions.

Artifacts:

```text
runs/m384_old_key_local_recovery_targets/old_key_recovery_corpus.npz
runs/m384_old_key_local_recovery_targets/old_key_recovery_targets.csv
runs/m384_old_key_local_recovery_targets/recovery_candidates.csv
runs/m384_old_key_local_recovery_targets/summary.json
```

## No-Update Smoke

The exported corpus loads through the M383 exact repair residual:

```text
runs/m384_old_key_recovery_no_update_smoke/summary.json
```

Key values:

```text
old_key_recovery_rows: 4
old_key_recovery_loss: 0.002272237
old_key_recovery_preferred_loss: 0.002272168
old_key_recovery_wrong_anchor_loss: 0.000000069
exact_lexicographic_pass: true
ppo_run: false
checkpoint_promoted: false
actor_inputs_changed: false
```

## Tests

Focused tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
  python -m pytest -q tests/test_old_key_recovery_targets.py \
  tests/test_exact_post_ppo_repair.py
```

Result:

```text
13 passed
```

## Decision

M384 completes the target export step. It admits a no-PPO repair proof probe
using the real M384 recovery target corpus.

Next:

```text
m385-old-key-recovery-residual-repair-probe
```
