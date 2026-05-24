# M504 Boundary Action-Sensitive Targeted Pair Triage

## Purpose

M504 tests whether the M503 boundary-pressure matched-current surface contains
source-diverse rows that are both:

1. one-shot wrong-history action-sensitive; and
2. close enough to the terminal clearance boundary for those action differences
   to matter.

No outcome gate, training, PPO, actor-input change, checkpoint update, or
checkpoint promotion is performed.

## Command

M504 first runs the existing M500 action-sensitive selector on the M503
combined surface:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.natural_wrong_history_action_sensitive_selector \
  --candidate-pairs-csv runs/m503_natural_boundary_pressure_matched_current_summary/combined_matched_pairs.csv \
  --checkpoint-policy m399=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --env-config-map boundary_short_reveal=configs/m502_natural_boundary_pressure_short_reveal_zero_relvel.json \
  --env-config-map boundary_warmup=configs/m502_natural_boundary_pressure_warmup_zero_relvel.json \
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
  --run-dir runs/m504_boundary_action_sensitive_targeted_pair_triage
```

## Artifacts

```text
runs/m504_boundary_action_sensitive_targeted_pair_triage/summary.json
runs/m504_boundary_action_sensitive_targeted_pair_triage/action_sensitive_candidates.csv
runs/m504_boundary_action_sensitive_targeted_pair_triage/targeted_pairs.csv
runs/m504_boundary_action_sensitive_targeted_pair_triage/invalid_snapshots.csv
```

## Result

M504 improves source balance and finds a few true boundary rows, but still fails
the boundary-action-sensitive targeted gate.

Summary:

```text
candidate_row_count:          22786
invalid_snapshot_row_count:     122
stage1_pass_count:             1042
trajectory_pass_count:          523
targeted_pair_count:            195

probe_seed_count:                 6
obstacle_label_count:             3
target_count:                     3
config_count:                     2
offset_count:                     4

single_seed_share:             0.317949
single_label_share:            0.538462
single_config_share:           0.579487

targeted_trajectory_mean:      0.224056
targeted_trajectory_p90:       0.348210
targeted_normal_margin_min:   -0.140489

source_diversity_gate_pass:    false
materially_stronger_baseline:  true
action_sensitive_surface_found:false
```

The source shares are acceptable, and the trajectory signal is materially above
the M498 baseline. The gate fails on count and boundary coverage:

```text
required targeted rows:        >= 240
actual targeted rows:             195

required rows normal_margin <= 0.50: >= 40
actual targeted rows <= 0.50:         4

required rows normal_margin <= 1.00: >= 100
actual targeted rows <= 1.00:         6
```

## Boundary Audit

The full M504 candidate table shows the problem is not only the final caps:

```text
stage1 rows:
  rows: 1042
  normal_margin <= 0.50: 5
  normal_margin <= 1.00: 12
  normal_margin <= 3.00: 65

trajectory-pass rows:
  rows: 523
  normal_margin <= 0.50: 4
  normal_margin <= 1.00: 10
  normal_margin <= 3.00: 25

targeted rows:
  rows: 195
  normal_margin <= 0.50: 4
  normal_margin <= 1.00: 6
  normal_margin <= 3.00: 12
```

The M502 boundary-pressure configs created a better matched-current surface
than M495, but they still do not naturally align wrong-history action
sensitivity with terminal-boundary sensitivity often enough.

## Interpretation

M504 rejects the direct targeted-triage path:

```text
wrong-history action sensitivity exists;
source diversity is acceptable;
but terminal-boundary rows are too sparse.
```

The next proof path should not run an outcome gate on M504 targeted rows. It
also should not keep tightening the same action-only selector. The blocker is
now terminal-boundary alignment: the research harness must mine or construct
states where normal-history clearance is already low and then test whether
wrong-history changes matter at those states.

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
m505-terminal-boundary-alignment-redesign
```
