# M514 Projected Label-Margin Conflict Audit

## Purpose

M514 audits the conflict found by M512: projected scenario-label diversity
exists, but it does not overlap with terminal-boundary low-margin rows.

This milestone is an audit only. No outcome gate, training, PPO,
actor-input change, checkpoint update, or checkpoint promotion is performed.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.projected_label_margin_conflict_audit \
  --source-pairs-csv runs/m508_terminal_boundary_anchor_miner/scored_pairs.csv \
  --checkpoint-policy m399=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --env-config-map boundary_short_reveal=configs/m502_natural_boundary_pressure_short_reveal_zero_relvel.json \
  --env-config-map boundary_warmup=configs/m502_natural_boundary_pressure_warmup_zero_relvel.json \
  --max-source-pairs 180 \
  --max-projected-candidates 0 \
  --device cpu \
  --run-dir runs/m514_projected_label_margin_conflict_audit
```

## Artifacts

```text
runs/m514_projected_label_margin_conflict_audit/summary.json
runs/m514_projected_label_margin_conflict_audit/source_pairs.csv
runs/m514_projected_label_margin_conflict_audit/projected_pairs.csv
runs/m514_projected_label_margin_conflict_audit/scored_pairs.csv
runs/m514_projected_label_margin_conflict_audit/label_margin_summary.csv
runs/m514_projected_label_margin_conflict_audit/margin_bucket_summary.csv
runs/m514_projected_label_margin_conflict_audit/low_margin_non_unavoidable_rows.csv
runs/m514_projected_label_margin_conflict_audit/invalid_snapshots.csv
```

## Implementation

M514 adds:

```text
src/autodrift/projected_label_margin_conflict_audit.py
tests/test_projected_label_margin_conflict_audit.py
```

The audit uses a broader diagnostic projection grid:

```text
body_x_absolute:
  3, 4, 5, 6, 8, 10, 12, 14, 16, 18

body_y_from_source:
  source_y - 2.0
  source_y - 1.5
  source_y - 1.0
  source_y - 0.5
  source_y + 0.0
  source_y + 0.5
  source_y + 1.0
  source_y + 1.5
  source_y + 2.0

half_width_scale:
  0.5, 0.75, 1.0, 1.25, 1.5
```

Projected labels are offline audit metadata only. They are not actor inputs.

## Result

Summary:

```text
source_pair_count:                  180
projected_candidate_count:        78490
scored_pair_count:                78490
projected_obstacle_label_count:       4

scored labels:
  unavoidable:    65979
  drift_required: 10609
  aeb_feasible:    1485
  aes_feasible:     417

non_unavoidable_row_count:        12511
non_unavoidable_min_normal_margin: 6.505553

low_margin_threshold:                 2.0
low_margin_non_unavoidable_count:       0
soft_low_margin_non_unavoidable_count:  0
low_margin_non_unavoidable_exists:  false

recommended_next_path:
  pre_register_proof_scenario_gate_split
```

## Label-Margin Summary

```text
unavoidable:
  row_count: 65979
  normal_margin_min: -0.334654
  margin <= 0.5: 13226
  margin <= 1.0: 18159
  margin <= 2.0: 27652
  margin <= 4.0: 37232

drift_required:
  row_count: 10609
  normal_margin_min: 6.505553
  margin <= 4.0: 0
  margin <= 8.0: 119

aeb_feasible:
  row_count: 1485
  normal_margin_min: 11.560831
  margin <= 8.0: 0

aes_feasible:
  row_count: 417
  normal_margin_min: 13.745194
  margin <= 8.0: 0
```

Margin buckets confirm the same pattern:

```text
(-inf,0.5]: unavoidable only
(0.5,1.0]: unavoidable only
(1.0,2.0]: unavoidable only
(2.0,4.0]: unavoidable only
(4.0,8.0]: 119 drift_required, 16627 unavoidable
(8.0,12.0]: aeb_feasible/drift_required/unavoidable
(12.0,inf): aeb_feasible/aes_feasible/drift_required/unavoidable
```

## Interpretation

M514 confirms the M512 diagnosis. Under the current M502 source states and
projection families, scenario-label diversity exists only away from the
terminal boundary. When rows are close enough to be useful for terminal-margin
wrong-history proof, the simulator scenario classifier calls them
`unavoidable`.

Therefore the next step should not relax the M512 label-diversity requirement
inside the same gate. The correct next step is to pre-register a split:

```text
mechanism proof gate:
  terminal-boundary margin sensitivity,
  source/config/target/geometry diversity,
  wrong-history action or margin effect.

scenario distribution gate:
  broad label diversity,
  non-boundary generalization,
  separate success/margin statistics.
```

The split must be documented before using it to admit a proof surface.

## Decision

```text
confirm_label_margin_conflict_admit_m515_proof_scenario_gate_split_design
```

Failure classification:

```text
none
```

Next blocker:

```text
m515-proof-scenario-gate-split-design
```
