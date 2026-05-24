# M508 Terminal-Boundary Anchor Miner

## Purpose

M508 implements and runs the M507 anchor-first terminal-boundary miner.

The goal is to test whether mining low-clearance normal-history states first
can produce a larger, source-diverse, one-shot wrong-history-sensitive boundary
surface than selecting from the existing M504 pair table.

No outcome gate, training, PPO, actor-input change, checkpoint update, or
checkpoint promotion is performed.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.terminal_boundary_anchor_miner \
  --checkpoint-policy m399=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --env-config-map boundary_short_reveal=configs/m502_natural_boundary_pressure_short_reveal_zero_relvel.json \
  --env-config-map boundary_warmup=configs/m502_natural_boundary_pressure_warmup_zero_relvel.json \
  --anchor-seeds 13000,13100,13200,13300,13400,13500 \
  --episodes-per-seed 64 \
  --snapshot-stride 2 \
  --anchor-margin-max 1.0 \
  --candidate-margin-max 2.0 \
  --nearest-k 48 \
  --max-current-distance-quantile 0.05 \
  --short-horizon-steps 8 \
  --device cpu \
  --run-dir runs/m508_terminal_boundary_anchor_miner
```

## Artifacts

```text
runs/m508_terminal_boundary_anchor_miner/summary.json
runs/m508_terminal_boundary_anchor_miner/source_rows.csv
runs/m508_terminal_boundary_anchor_miner/anchor_candidates.csv
runs/m508_terminal_boundary_anchor_miner/anchors.csv
runs/m508_terminal_boundary_anchor_miner/candidate_pairs.csv
runs/m508_terminal_boundary_anchor_miner/scored_pairs.csv
runs/m508_terminal_boundary_anchor_miner/targeted_pairs.csv
runs/m508_terminal_boundary_anchor_miner/invalid_anchor_snapshots.csv
runs/m508_terminal_boundary_anchor_miner/invalid_pair_snapshots.csv
```

## Implementation

M508 adds:

```text
src/autodrift/terminal_boundary_anchor_miner.py
tests/test_terminal_boundary_anchor_miner.py
```

The miner uses the current public-gate base checkpoint and keeps the P0 actor
contract unchanged. It writes seed/step rows that can be reconstructed from the
simulator; it does not serialize hidden states into the actor input or create a
new checkpoint.

The implemented flow is:

```text
1. collect P0 source rows from both M502 boundary-pressure configs;
2. filter obstacle-visible decision-window candidates;
3. reconstruct snapshots and replay normal history for 8 steps;
4. keep anchors with normal_min_clearance_margin <= 1.0;
5. find nearest wrong-history source rows in current_response_context space;
6. require target_z_delta >= 1.0 and visible-distance quantile <= 0.05;
7. replay normal and one-shot wrong_matched_history for 8 steps;
8. select source-capped low-margin/action-sensitive targeted rows.
```

## Result

Summary:

```text
source_row_count:              25081
anchor_candidate_row_count:     9600
normal_scored_anchor_count:     9600
anchor_count:                   3246

candidate_pair_count:           3000
scored_pair_count:              3000
pair_count:                      104

probe_seed_count:                  6
obstacle_label_count:              2
target_count:                      3
config_count:                      2

single_seed_share:             0.375000
single_label_share:            0.826923
single_config_share:           0.596154

rows normal margin <= 0.50:         97
rows normal margin <= 1.00:        104

targeted_trajectory_mean:       0.092899
targeted_trajectory_p90:        0.130059
targeted_first_action_mean:     0.107321
targeted_normal_margin_min:    -0.191871
targeted_normal_margin_p50:     0.137000

terminal_boundary_anchor_gate_pass: false
outcome_gate_admitted:             false
```

Source distribution:

```text
targeted_by_probe_seed:
  13000: 21
  13100: 39
  13200: 12
  13300: 8
  13400: 8
  13500: 16

targeted_by_left_obstacle_label:
  drift_required: 18
  unavoidable: 86

targeted_by_config:
  boundary_short_reveal: 62
  boundary_warmup: 42
```

The pre-registered gate fails because:

```text
pair_count:          104 < 240
single_label_share:  0.826923 > 0.70
```

The low-margin and action-signal parts do not fail:

```text
anchor_count:                 3246 >= 120
rows margin <= 0.50:            97 >= 40
rows margin <= 1.00:           104 >= 100
targeted_trajectory_mean: 0.092899 >= 0.04
targeted_trajectory_p90:  0.130059 >= 0.08
```

## Audit

The scored pair table has many eligible rows before source caps:

```text
scored_pair_count: 3000
margin <= 0.50:   2752
margin <= 1.00:   3000
soft-action eligible at default thresholds: 2220
```

But those rows collapse into a small set of obstacle geometry buckets:

```text
eligible obstacle_bucket_count: 5

top buckets:
  distance=0.000-5.000|lateral=-2.000--1.000: 1509
  distance=0.000-5.000|lateral=-3.000--2.000:  575
  distance=0.000-5.000|lateral=-1.000-0.000:    69
  distance=-5.000-0.000|lateral=-3.000--2.000:  59
  distance=-5.000-0.000|lateral=-2.000--1.000:   8
```

So M508 changes the failure mode. M506 was candidate-surface small. M508 has
many natural boundary anchors and nonzero one-shot wrong-history action signal,
but the natural low-clearance states are concentrated in a few late obstacle
geometry buckets and are label-imbalanced after source caps.

## Interpretation

M508 rejects outcome-gate admission. It should not be converted into a proof
surface by relaxing caps after seeing the result.

The result supports the M507 fallback path: use controlled obstacle-boundary
projection around natural M508 anchors, with strict geometry-change limits and
an explicit projection-proof label. The projection branch must report how much
the obstacle geometry was moved and must not be described as raw natural
scenario proof.

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
m509-obstacle-boundary-projection-design
```
