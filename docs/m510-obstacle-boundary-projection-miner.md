# M510 Obstacle-Boundary Projection Miner

## Purpose

M510 implements and runs the bounded obstacle-boundary projection miner designed
in M509.

The goal is to test whether starting from M508 natural anchors and relocating
only obstacle geometry can produce a source-diverse terminal-boundary
wrong-history-sensitive projection surface.

No outcome gate, training, PPO, actor-input change, checkpoint update, or
checkpoint promotion is performed.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.obstacle_boundary_projection_miner \
  --source-pairs-csv runs/m508_terminal_boundary_anchor_miner/scored_pairs.csv \
  --checkpoint-policy m399=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --env-config-map boundary_short_reveal=configs/m502_natural_boundary_pressure_short_reveal_zero_relvel.json \
  --env-config-map boundary_warmup=configs/m502_natural_boundary_pressure_warmup_zero_relvel.json \
  --device cpu \
  --run-dir runs/m510_obstacle_boundary_projection_miner
```

## Artifacts

```text
runs/m510_obstacle_boundary_projection_miner/summary.json
runs/m510_obstacle_boundary_projection_miner/source_pairs.csv
runs/m510_obstacle_boundary_projection_miner/projected_pairs.csv
runs/m510_obstacle_boundary_projection_miner/scored_pairs.csv
runs/m510_obstacle_boundary_projection_miner/targeted_pairs.csv
runs/m510_obstacle_boundary_projection_miner/invalid_snapshots.csv
```

## Implementation

M510 adds:

```text
src/autodrift/obstacle_boundary_projection_miner.py
tests/test_obstacle_boundary_projection_miner.py
```

The miner:

```text
1. loads M508 scored natural pairs;
2. reconstructs left/right OutcomeSnapshots from seed/step;
3. relocates only the left snapshot obstacle in body coordinates;
4. recomputes the P0 observation from the simulator state;
5. replays normal and one-shot wrong_matched_history for 8 steps;
6. writes projection metadata and source-capped targeted rows.
```

Projection metadata includes:

```text
proof_surface_type = obstacle_boundary_projection
snapshot_relocated = true
source_obstacle_body_x / y
projected_obstacle_body_x / y
projection_dx / dy / l2
projection_family
projection_bucket
```

## Result

Summary:

```text
source_pair_count:             600
projected_candidate_count:    5000
scored_pair_count:            5000
pair_count:                    102

probe_seed_count:                6
obstacle_label_count:            1
target_count:                    3
config_count:                    2

single_seed_share:           0.362745
single_label_share:          1.000000
single_config_share:         0.588235

rows normal margin <= 0.50:       93
rows normal margin <= 1.00:      102

targeted_trajectory_mean:     0.089577
targeted_trajectory_p90:      0.125161
targeted_first_action_mean:   0.100314
targeted_normal_margin_min:  -0.253192
targeted_normal_margin_p50:  -0.039579

projection_l2_p50:            1.000000
projection_l2_p90:            1.118034
primary_projection_share:     1.000000

projection_gate_pass: false
outcome_gate_admitted: false
```

The pre-registered gate fails because:

```text
pair_count:             102 < 240
obstacle_label_count:     1 < 2
single_label_share:   1.000 > 0.70
```

The projection magnitude and action-signal constraints do not fail:

```text
projection_l2_p50:        1.000000 <= 3.0
projection_l2_p90:        1.118034 <= 6.0
primary_projection_share: 1.000000 >= 0.80
targeted_trajectory_mean: 0.089577 >= 0.04
targeted_trajectory_p90:  0.125161 >= 0.08
```

## Audit

All scored projected rows are classified as `unavoidable`:

```text
projected labels:
  unavoidable: 5000

targeted labels:
  unavoidable: 102
```

This is not because M508 source rows have no drift-required examples:

```text
M508 scored source labels:
  drift_required: 650
  unavoidable:   2350

M508 soft-action rows at margin <= 1.0:
  drift_required: 432
  unavoidable:   1788
```

M510's small bounded geometry moves preserve tight projection magnitude, but
they do not cross scenario-label boundaries. The selected rows remain useful as
unavoidable projection diagnostics, but they cannot admit an outcome gate under
the source-diversity rules.

## Interpretation

M510 rejects outcome-gate admission. The next step should not relax the label
gate or claim the unavoidable-only surface as sufficient.

The next miner should explicitly target label-balanced projected families while
still preserving natural ego/history state. It should solve for bounded
obstacle distance/lateral/width variants that produce at least two projected
scenario labels, then report how much geometry change was required.

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
m511-label-targeted-projection-design
```
