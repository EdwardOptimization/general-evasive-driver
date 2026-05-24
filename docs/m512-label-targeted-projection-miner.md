# M512 Label-Targeted Projection Miner

## Purpose

M512 implements and runs the label-targeted projection miner designed in M511.

The goal is to test whether explicitly enumerating projected obstacle distance,
lateral offset, and half-width can create a source-diverse terminal-boundary
projection surface with at least two projected scenario labels.

No outcome gate, training, PPO, actor-input change, checkpoint update, or
checkpoint promotion is performed.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.label_targeted_projection_miner \
  --source-pairs-csv runs/m508_terminal_boundary_anchor_miner/scored_pairs.csv \
  --checkpoint-policy m399=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --env-config-map boundary_short_reveal=configs/m502_natural_boundary_pressure_short_reveal_zero_relvel.json \
  --env-config-map boundary_warmup=configs/m502_natural_boundary_pressure_warmup_zero_relvel.json \
  --max-source-pairs 300 \
  --max-projected-candidates 0 \
  --device cpu \
  --run-dir runs/m512_label_targeted_projection_miner
```

## Artifacts

```text
runs/m512_label_targeted_projection_miner/summary.json
runs/m512_label_targeted_projection_miner/source_pairs.csv
runs/m512_label_targeted_projection_miner/projected_pairs.csv
runs/m512_label_targeted_projection_miner/scored_pairs.csv
runs/m512_label_targeted_projection_miner/targeted_pairs.csv
runs/m512_label_targeted_projection_miner/invalid_snapshots.csv
```

## Implementation

M512 adds:

```text
src/autodrift/label_targeted_projection_miner.py
tests/test_label_targeted_projection_miner.py
```

It also extends `obstacle_boundary_projection_miner.score_projected_pairs` to
support `half_width_scale` and record:

```text
source_obstacle_half_width
projected_obstacle_half_width
half_width_scale
half_width_delta_abs
```

Projected labels remain offline mining/gate metadata only. They are not actor
inputs.

## Result

Summary:

```text
source_pair_count:                  300
projected_candidate_count:        35967
scored_pair_count:                35967
pair_count:                         123

probe_seed_count:                     6
projected_obstacle_label_count:       1
target_count:                         3
config_count:                         2

single_seed_share:                0.325203
single_projected_label_share:     1.000000
single_config_share:              0.528455

rows normal margin <= 0.50:           73
rows normal margin <= 1.00:           95

targeted_trajectory_mean:         0.066786
targeted_trajectory_p90:          0.108503

projection_l2_p50:                1.672650
projection_l2_p90:                3.075420
half_width_delta_abs_p90:         0.339745
primary_projection_share:         1.000000

projection_gate_pass: false
outcome_gate_admitted: false
```

The pre-registered gate fails because:

```text
pair_count:                       123 < 240
projected_obstacle_label_count:     1 < 2
single_projected_label_share:    1.000 > 0.70
rows normal margin <= 1.00:         95 < 100
```

## Audit

M512 does find multiple projected labels in the scored table:

```text
unavoidable:    33088
drift_required:  2102
aeb_feasible:     777
```

But all low-margin projected rows are `unavoidable`:

```text
normal_margin <= 0.50:
  unavoidable: 4543

normal_margin <= 1.00:
  unavoidable: 5702

normal_margin <= 2.00:
  unavoidable: 10174

normal_margin <= 4.00:
  unavoidable: 17049
```

The first non-`unavoidable` labels only appear at high margins:

```text
drift_required min normal margin: 7.450602
aeb_feasible   min normal margin: 7.458511
```

So M512 confirms the current blocker: under the M502 projection family,
projected-label diversity and terminal-boundary low-margin selection conflict.
The label-targeted grid can produce `drift_required` / `aeb_feasible` labels,
but not near the obstacle boundary where wrong-history action sensitivity can
be converted into terminal-margin proof.

## Interpretation

M512 rejects outcome-gate admission. The next step should not relax label
diversity or margin gates inside M512 after seeing this result.

The next milestone should audit the label/margin conflict directly: determine
whether non-`unavoidable` projected labels with low normal margin are impossible
under the current scenario classifier and M502 geometry, or whether the grid is
still missing the right projection family.

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
m513-projected-label-margin-conflict-design
```
