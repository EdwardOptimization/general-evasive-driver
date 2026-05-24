# M506 Terminal-Boundary-Aware Selector

## Purpose

M506 implements and runs the M505 terminal-boundary-aware selector. It reverses
the M504 selection order:

```text
first:  require low normal-history clearance margin
then:   require smaller but nonzero one-shot wrong-history action movement
```

No outcome gate, training, PPO, actor-input change, checkpoint update, or
checkpoint promotion is performed.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.terminal_boundary_aware_selector \
  --candidate-rows-csv runs/m504_boundary_action_sensitive_targeted_pair_triage/action_sensitive_candidates.csv \
  --max-normal-margin 2.0 \
  --first-action-threshold 0.04 \
  --trajectory-mean-threshold 0.04 \
  --trajectory-max-threshold 0.08 \
  --max-rows 300 \
  --max-per-probe-seed 60 \
  --max-per-left-seed 6 \
  --max-per-label 150 \
  --max-per-target 130 \
  --max-per-config 160 \
  --max-per-offset 90 \
  --max-per-obstacle-bucket 20 \
  --min-targeted-rows 240 \
  --min-probe-seed-count 6 \
  --min-obstacle-label-count 2 \
  --min-target-count 2 \
  --min-config-count 2 \
  --max-single-seed-share 0.50 \
  --max-single-label-share 0.70 \
  --max-single-config-share 0.70 \
  --min-margin-le-0-50-rows 40 \
  --min-margin-le-1-00-rows 100 \
  --min-margin-le-2-00-rows 180 \
  --min-trajectory-mean 0.04 \
  --min-trajectory-p90 0.08 \
  --run-dir runs/m506_terminal_boundary_aware_selector
```

## Artifacts

```text
runs/m506_terminal_boundary_aware_selector/summary.json
runs/m506_terminal_boundary_aware_selector/terminal_boundary_candidates.csv
runs/m506_terminal_boundary_aware_selector/targeted_pairs.csv
```

## Implementation

M506 adds:

```text
src/autodrift/terminal_boundary_aware_selector.py
tests/test_terminal_boundary_aware_selector.py
```

The selector filters:

```text
normal_min_clearance_margin <= 2.0
```

and then accepts rows with any soft action signal:

```text
first_action_distance >= 0.04
or action_trajectory_distance_mean >= 0.04
or action_trajectory_distance_max >= 0.08
```

## Result

M506 improves terminal-boundary alignment relative to M504, but it still does
not produce a source-capped surface large enough for outcome testing.

Summary:

```text
candidate_row_count:                  494
targeted_pair_count:                  101

probe_seed_count:                       6
obstacle_label_count:                   2
target_count:                           3
config_count:                           2

single_seed_share:                   0.198020
single_label_share:                  0.732673
single_config_share:                 0.673267

targeted_rows_normal_margin <= 0.50:   35
targeted_rows_normal_margin <= 1.00:   76
targeted_rows_normal_margin <= 2.00:  101

targeted_trajectory_mean:           0.084141
targeted_trajectory_p90:            0.138282
targeted_normal_margin_min:        -0.204788
targeted_normal_margin_p50:         0.869409

terminal_boundary_gate_pass: false
```

The result is better than M504 on margin alignment:

```text
M504 targeted rows margin <= 0.50: 4
M506 targeted rows margin <= 0.50: 35

M504 targeted rows margin <= 1.00: 6
M506 targeted rows margin <= 1.00: 76
```

But the pre-registered gate requires:

```text
targeted_pair_count >= 240
rows margin <= 0.50 >= 40
rows margin <= 1.00 >= 100
rows margin <= 2.00 >= 180
single_label_share <= 0.70
```

M506 fails all of those except the trajectory signal.

## Interpretation

The M506 selector confirms the M505 diagnosis: low-margin rows exist and small
wrong-history action perturbations exist, but the existing M504 candidate table
does not contain enough source-diverse low-margin/action-sensitive rows after
source caps.

The next step should not relax caps or run an outcome gate on 101 rows. It
should build the next candidate pool from terminal-boundary anchors directly:

```text
mine low-clearance normal-history states first;
then search for wrong histories that perturb actions at those states.
```

If that is still insufficient, the fallback is obstacle-boundary projection
with strict source-diversity and geometry-change limits.

## Decision

```text
reject_outcome_gate_admission
```

Failure classification:

```text
scenario_sampling_failure
```

Next blocker:

```text
m507-terminal-boundary-anchor-mining-design
```
