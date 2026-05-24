# M500 Natural Action-Sensitive Selector Implementation

## Purpose

M500 implements and runs the M499 action-sensitive selector on the full M495
natural belief matched-current surface.

No training, PPO, actor-input change, checkpoint update, or checkpoint
promotion is performed.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.natural_wrong_history_action_sensitive_selector \
  --candidate-pairs-csv runs/m495_natural_belief_matched_current_summary/combined_matched_pairs.csv \
  --checkpoint-policy m399=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --env-config-map short_reveal=configs/m494_natural_belief_short_reveal_zero_relvel.json \
  --env-config-map warmup_capability=configs/m494_natural_belief_warmup_capability_zero_relvel.json \
  --decision-offsets 0,2,4,8 \
  --short-horizon-steps 8 \
  --first-action-threshold 0.12 \
  --trajectory-mean-threshold 0.12 \
  --trajectory-max-threshold 0.25 \
  --max-rows 360 \
  --max-per-probe-seed 70 \
  --max-per-left-seed 8 \
  --max-per-label 160 \
  --max-per-target 140 \
  --max-per-config 180 \
  --max-per-offset 100 \
  --max-per-obstacle-bucket 24 \
  --min-targeted-rows 240 \
  --min-probe-seed-count 6 \
  --min-obstacle-label-count 2 \
  --min-target-count 2 \
  --min-config-count 2 \
  --min-offset-count 2 \
  --max-single-seed-share 0.50 \
  --max-single-label-share 0.70 \
  --max-single-config-share 0.70 \
  --baseline-trajectory-mean 0.055405 \
  --device cpu \
  --run-dir runs/m500_natural_action_sensitive_selector
```

## Artifacts

```text
runs/m500_natural_action_sensitive_selector/summary.json
runs/m500_natural_action_sensitive_selector/action_sensitive_candidates.csv
runs/m500_natural_action_sensitive_selector/targeted_pairs.csv
runs/m500_natural_action_sensitive_selector/invalid_snapshots.csv
```

## Implementation

M500 adds:

```text
src/autodrift/natural_wrong_history_action_sensitive_selector.py
tests/test_natural_wrong_history_action_sensitive_selector.py
```

The selector:

1. reads the full M495 matched-current pair surface;
2. reconstructs left/right snapshots at decision offsets `0`, `2`, `4`, and
   `8`;
3. compares a normal branch against a one-shot `wrong_matched_history` branch;
4. records first-action distance, short-horizon action trajectory distance,
   and short-horizon margin gap;
5. exports source-capped targeted rows only if the action-sensitive surface is
   strong enough and source-diverse enough.

## Result

M500 found action-sensitive rows, but did not find a source-diverse or
near-boundary surface suitable for another outcome gate.

Key summary:

```text
candidate_row_count:          22133
invalid_snapshot_row_count:     187
stage1_pass_count:              885
trajectory_pass_count:          481
targeted_pair_count:            171

probe_seed_count:                 6
obstacle_label_count:             3
target_count:                     3
config_count:                     2
offset_count:                     4

single_seed_share:             0.269006
single_label_share:            0.538012
single_config_share:           0.725146

targeted_trajectory_mean:      0.228203
targeted_trajectory_p90:       0.360038
targeted_normal_margin_min:    0.932188

source_diversity_gate_pass:    false
materially_stronger_baseline:  true
action_sensitive_surface_found:false
```

The selected rows are materially stronger than the M498 weak wrong-history
trajectory baseline:

```text
M498 wrong-history trajectory mean: 0.055405
M500 targeted trajectory mean:      0.228203
```

But the surface fails admission:

```text
required targeted rows:        >= 240
actual targeted rows:             171

required single_config_share:  <= 0.70
actual single_config_share:       0.725146
```

The more important blocker is that these action-sensitive rows are not close
to the outcome boundary:

```text
eligible rows with normal_margin <= 0.25: 0
targeted rows with normal_margin <= 0.25: 0
targeted_normal_margin_min:             0.932188
```

## Interpretation

The M499 selector improved the action signal, but the signal mostly lives in
high-clearance rows. That is not enough for self-ID outcome proof. If another
outcome gate were run directly on M500 targeted rows, it would likely repeat
the same failure pattern: wrong-history changes actions, but the normal branch
has too much clearance slack for those changes to create collision,
completion, or success-drop evidence.

This is a useful negative result:

```text
target-z divergence alone is insufficient;
first-action/trajectory divergence alone is also insufficient;
the selector must jointly target action sensitivity and terminal boundary
sensitivity.
```

## Decision

```text
reject_outcome_gate_admission
```

M500 does not admit an M501 outcome gate.

Failure classification:

```text
scenario_sampling_failure
```

Next blocker:

```text
m501-natural-boundary-action-sensitive-redesign
```

M501 should redesign the natural surface around rows that are both:

1. one-shot wrong-history action-sensitive; and
2. near enough to the terminal/outcome boundary that those action differences
   can matter.
