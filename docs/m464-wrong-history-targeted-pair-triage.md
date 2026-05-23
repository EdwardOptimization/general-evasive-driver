# M464 Wrong-History Targeted Pair Triage

## Purpose

M464 implements the targeted pair triage designed in M463. It does not run
training or promote a checkpoint. It creates a source-diverse matched-current
pair surface from the full M462 `candidate_pairs.csv` pool for a later
wrong-history outcome probe.

## Contract

- Actor inputs are unchanged.
- Hidden parameters, oracle labels, TTC, references, and controller modes are
  not added to the deployable actor.
- Obstacle labels and target response metrics are used only for offline mining
  and diversity accounting.
- Reset/zero-current diagnostics are not treated as wrong-history proof.

## Implementation

Added:

```text
src/autodrift/wrong_history_targeted_pair_triage.py
tests/test_wrong_history_targeted_pair_triage.py
```

The CLI consumes `candidate_pairs.csv` and writes:

```text
target_candidates.csv
targeted_pairs.csv
summary.json
```

Hard filters:

```text
target_z_delta >= min_target_z_delta
visible_distance <= row visible_threshold
left_episode != right_episode
```

Score:

```text
wrong_history_target_score =
  hidden_gap_score
+ 0.25 * hidden_more_score
+ 0.35 * target_z_score
+ 0.30 * near_boundary_proxy
+ label_priority_score
+ 0.15 * visible_similarity_score
```

The selector then applies source caps over probe seed, left seed, obstacle
label, target, and obstacle bucket.

## Smoke Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.wrong_history_targeted_pair_triage \
  --candidate-pairs-csv runs/m462_late_reveal_matched_current_fresh_seed10200/candidate_pairs.csv \
  --min-target-z-delta 1.0 \
  --max-rows 240 \
  --max-per-probe-seed 90 \
  --max-per-left-seed 8 \
  --max-per-label 120 \
  --max-per-target 90 \
  --max-per-obstacle-bucket 18 \
  --min-targeted-rows 180 \
  --min-probe-seed-count 3 \
  --min-obstacle-label-count 2 \
  --min-target-count 3 \
  --max-single-seed-share 0.50 \
  --max-single-label-share 0.60 \
  --run-dir runs/m464_wrong_history_targeted_pair_triage
```

## Results

```text
candidate pairs:             73281
eligible pairs:                618
targeted pairs:                209
targeted probe seeds:            3
targeted obstacle labels:        3
targeted targets:                3
single seed share:        0.377990
single label share:       0.574163
triage_pass:                 True
```

Targeted pairs by probe seed:

```text
10200: 79
10300: 78
10400: 52
```

Targeted pairs by obstacle label:

```text
drift_required: 120
aes_feasible:    53
unavoidable:     36
```

Targeted pairs by target:

```text
future_yaw_response:           90
future_braking_deceleration:   74
future_lateral_accel_response: 45
```

Artifacts:

```text
runs/m464_wrong_history_targeted_pair_triage/target_candidates.csv
runs/m464_wrong_history_targeted_pair_triage/targeted_pairs.csv
runs/m464_wrong_history_targeted_pair_triage/summary.json
```

## Interpretation

M464 succeeds as a source-diverse triage step. Compared with M462's weak
wrong-history accepted rows, this surface is no longer single-seed or
single-label. It is still only a pair surface, not outcome proof. The next step
must run action and continuation outcome interventions on this targeted pair
set and report wrong-history separately from reset/zero-current diagnostics.

## Validation

```text
tests/test_wrong_history_targeted_pair_triage.py: 4 passed
```

## Decision

```text
triage_pass_admit_m465_targeted_wrong_history_outcome_probe
```

No checkpoint is promoted.
