# M486 Critical-Window Targeted Pair Triage

## Purpose

M486 selects a source-diverse targeted wrong-history pair surface from the M485
critical-window matched-current surface.

No training, PPO, actor-input change, outcome/tail gate, checkpoint update, or
checkpoint promotion is performed.

## Command

```bash
PYTHONPATH=src python -m autodrift.wrong_history_targeted_pair_triage \
  --candidate-pairs-csv runs/m485_critical_window_matched_current_summary/combined_matched_pairs.csv \
  --min-target-z-delta 1.0 \
  --obstacle-distance-ceiling 30.0 \
  --max-rows 360 \
  --max-per-probe-seed 70 \
  --max-per-left-seed 8 \
  --max-per-label 160 \
  --max-per-target 140 \
  --max-per-obstacle-bucket 24 \
  --obstacle-distance-bucket-width 5.0 \
  --obstacle-lateral-bucket-width 1.0 \
  --min-targeted-rows 240 \
  --min-probe-seed-count 6 \
  --min-obstacle-label-count 2 \
  --min-target-count 2 \
  --max-single-seed-share 0.50 \
  --max-single-label-share 0.70 \
  --run-dir runs/m486_critical_window_targeted_pair_triage
```

Artifacts:

```text
runs/m486_critical_window_targeted_pair_triage/summary.json
runs/m486_critical_window_targeted_pair_triage/target_candidates.csv
runs/m486_critical_window_targeted_pair_triage/targeted_pairs.csv
```

## Results

```text
candidate pairs:              5802
eligible pairs:               5802
targeted pairs:                312
probe seeds:                     6
obstacle labels:                 3
targets:                         3
single-seed share:        0.195513
single-label share:       0.512821
triage pass:                  true
```

By critical config:

```text
near_threshold:   157
late_high_energy: 155
```

By seed:

```text
11200: 60
11300: 44
11400: 44
11500: 61
11600: 46
11700: 57
```

By label:

```text
drift_required: 160
unavoidable:    137
aes_feasible:    15
```

By target:

```text
future_braking_deceleration: 140
future_yaw_response:        140
future_lateral_accel:        32
```

## Interpretation

M486 passes the targeted-surface gate. It provides a balanced pair set for
tail-aligned wrong-history outcome testing:

```text
>= 240 targeted rows
6 probe seeds
3 labels
3 targets
balanced near_threshold / late_high_energy split
single-seed and single-label shares below caps
```

This is still not self-ID proof. It only selects where to test tail-aligned
wrong-history interventions next.

## Decision

```text
critical_window_targeted_triage_pass_admit_m487_tail_aligned_outcome_gate
```

M487 should split `targeted_pairs.csv` by `critical_config` and run
tail-aligned wrong-history outcome gates on each config, then combine the
source-diversity and event-proof results.

No checkpoint is promoted.
