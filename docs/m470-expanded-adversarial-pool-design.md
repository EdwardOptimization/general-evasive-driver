# M470 Expanded Adversarial Pool Design

## Purpose

M470 designs the next step after M469 found the adversarial wrong-history pair
surface too small and seed-imbalanced. The next step should expand the
candidate pool before any outcome probe, not loosen the gate or run PPO.

No training, PPO, checkpoint update, actor-input change, or checkpoint
promotion is performed.

## M469 Failure Mode

M469 searched the full M462 candidate pool around M467 near-boundary anchors:

```text
search candidates:             50
adversarial pairs:             50
near-boundary left states:     26
probe seeds:                    3
labels:                         2
targets:                        3
single seed share:           0.68
search_pass:                False
```

The surface failed because:

```text
adversarial_pair_count < 64
single_seed_share > 0.50
```

This should be treated as a data-pool coverage failure. The 50-row surface is
not source-diverse enough for outcome probing.

## Design Choice

The most direct next test is an expanded same-window mining pass:

```text
same probe seeds:   10200, 10300, 10400
same env config:    configs/m457_history_necessity_late_reveal_zero_relvel.json
same checkpoint:    runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
more episodes:      80 instead of 40
more samples:       2400 instead of 1200
larger nearest_k:   32 instead of 12
```

Then rerun the existing adversarial search:

```text
anchors:
  runs/m467_near_boundary_wrong_history_selector/near_boundary_no_effect.csv

candidate pool:
  runs/m471_expanded_matched_current_seed10200/candidate_pairs.csv
```

This keeps the test narrow and interpretable:

- If M471 passes, the issue was M462 pool size.
- If M471 fails, the current seed window likely lacks enough wrong-history
  alternatives and the next step should add fresh seed windows or alter the
  scenario distribution.

## M471 Commands

Expanded matched-current mining:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.matched_current_response_ambiguity \
  --checkpoint-policy m399=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --env-config configs/m457_history_necessity_late_reveal_zero_relvel.json \
  --probe-seeds 10200,10300,10400 \
  --episodes 80 \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 2400 \
  --nearest-k 32 \
  --match-feature-set current_response_context \
  --max-visible-quantile 0.05 \
  --min-target-z-delta 1.0 \
  --max-pairs-per-target 640 \
  --max-pairs-per-physical-pair 2 \
  --max-pairs-per-left-step 40 \
  --max-pairs-per-source-obstacle-bucket 80 \
  --obstacle-distance-bucket-width 5.0 \
  --obstacle-lateral-bucket-width 1.0 \
  --min-accepted-pairs 120 \
  --device cpu \
  --run-dir runs/m471_expanded_matched_current_seed10200
```

Adversarial search:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.adversarial_wrong_history_pair_search \
  --near-boundary-csv runs/m467_near_boundary_wrong_history_selector/near_boundary_no_effect.csv \
  --candidate-pairs-csv runs/m471_expanded_matched_current_seed10200/candidate_pairs.csv \
  --normal-margin-ceiling 0.75 \
  --min-target-z-delta 1.0 \
  --max-rows 160 \
  --max-per-anchor 4 \
  --max-per-probe-seed 72 \
  --max-per-label 112 \
  --max-per-target 72 \
  --max-per-obstacle-bucket 28 \
  --min-adversarial-pairs 64 \
  --min-left-state-count 16 \
  --min-probe-seed-count 3 \
  --min-obstacle-label-count 2 \
  --min-target-count 2 \
  --max-single-seed-share 0.50 \
  --max-single-label-share 0.70 \
  --run-dir runs/m471_expanded_adversarial_wrong_history_search
```

## M471 Pass Criteria

M471 should pass only if the adversarial surface is source-diverse enough for
outcome probing:

```text
adversarial_pairs >= 64
near_boundary_left_state_count >= 16
probe_seed_count >= 3
left_obstacle_label_count >= 2
target_count >= 2
single_seed_share <= 0.50
single_label_share <= 0.70
```

If M471 passes, M472 may run targeted action/outcome probes. If M471 fails,
M472 should be a fresh-seed or task-distribution redesign, not an outcome
probe.

## Decision

```text
admit_m471_expanded_adversarial_pool_run
```

No checkpoint is promoted.
