# M496 Natural Belief Targeted Pair Triage

## Purpose

M496 selects a source-diverse targeted wrong-history pair surface from the M495
natural belief matched-current surface.

No outcome gate, training, PPO, actor-input change, checkpoint update, or
checkpoint promotion is performed.

## Command

```bash
PYTHONPATH=src python -m autodrift.wrong_history_targeted_pair_triage \
  --candidate-pairs-csv runs/m495_natural_belief_matched_current_summary/combined_matched_pairs.csv \
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
  --run-dir runs/m496_natural_belief_targeted_pair_triage
```

After the tool run, M496 adds an explicit config/seed-window balance audit
because `wrong_history_targeted_pair_triage` gates seed and label balance but
does not gate config balance directly.

Artifacts:

```text
runs/m496_natural_belief_targeted_pair_triage/summary.json
runs/m496_natural_belief_targeted_pair_triage/target_candidates.csv
runs/m496_natural_belief_targeted_pair_triage/targeted_pairs.csv
```

## Results

```text
candidate pairs:              5580
eligible pairs:               5580
targeted pairs:                294
probe seeds:                     6
obstacle labels:                 3
targets:                         3
configs:                         2
seed windows:                    2
single-seed share:        0.238095
single-label share:       0.544218
single-config share:      0.605442
triage pass:                  true
config balance pass:          true
full natural triage pass:     true
```

By config:

```text
warmup_capability: 178
short_reveal:      116
```

By seed:

```text
11800: 46
11900: 48
12000: 46
12100: 70
12200: 64
12300: 20
```

By label:

```text
drift_required: 160
unavoidable:    122
aes_feasible:    12
```

By target:

```text
future_braking_deceleration: 140
future_yaw_response:        140
future_lateral_accel:        14
```

## Interpretation

M496 passes the targeted-surface gate. It provides a balanced pair set for
natural decision-window outcome testing:

```text
>= 240 targeted rows
6 probe seeds
3 labels
3 targets
2 configs
single-seed, single-label, and single-config shares below caps
```

This is still not self-ID proof. It only selects where to test whether
wrong-history, reset-hidden, or zero-current-response interventions create
outcome degradation in the natural decision window.

## Decision

```text
natural_belief_targeted_triage_pass_admit_m497_decision_window_outcome_gate
```

M497 should split `targeted_pairs.csv` by `config` and run decision-window
wrong-history outcome gates on each M494 config. Use early offsets around the
matched decision point before current-response correction can dominate.

No checkpoint is promoted.
