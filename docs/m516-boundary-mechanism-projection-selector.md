# M516 Boundary Mechanism Projection Selector

## Purpose

M516 implements the proof/scenario split pre-registered in M515. It selects a
terminal-boundary mechanism proof surface from M514 projected rows using
source/config/target/geometry diversity, without requiring projected
scenario-label diversity.

This milestone does not run an outcome gate, train, change actor inputs, update
a checkpoint, or promote a checkpoint.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.boundary_mechanism_projection_selector \
  --scored-pairs-csv runs/m514_projected_label_margin_conflict_audit/scored_pairs.csv \
  --run-dir runs/m516_boundary_mechanism_projection_selector
```

## Artifacts

```text
runs/m516_boundary_mechanism_projection_selector/summary.json
runs/m516_boundary_mechanism_projection_selector/boundary_mechanism_candidates.csv
runs/m516_boundary_mechanism_projection_selector/targeted_pairs.csv
```

## Implementation

M516 adds:

```text
src/autodrift/boundary_mechanism_projection_selector.py
tests/test_boundary_mechanism_projection_selector.py
```

The selector:

1. reads the already-scored M514 projected rows;
2. keeps terminal-boundary rows with `normal_min_clearance_margin <= 2.0`;
3. requires soft wrong-history action signal;
4. keeps bounded projection rows with `projection_l2 <= 6.0` and
   `half_width_delta_abs <= 0.8`;
5. builds projected obstacle geometry buckets and projection buckets;
6. uses a coverage-first selection pass so rare seeds, targets, configs, and
   geometry buckets are represented before high-score fill rows consume caps;
7. reports projected scenario labels but does not use label diversity as a
   mechanism proof gate.

The first greedy implementation selected only `112` rows because high-score
braking rows consumed caps before rare target/geometry groups were represented.
That was an implementation issue, not a data limitation. The final selector is
coverage-first, then score-fill.

## Result

Summary:

```text
scored_pair_count:                 78490
candidate_row_count:               20488
targeted_pair_count:                 292
probe_seed_count:                      6
target_count:                          3
config_count:                          2
projected_obstacle_bucket_count:      12
projection_bucket_count:              46

single_seed_share:                 0.273973
single_config_share:               0.650685
single_target_share:               0.445205
single_obstacle_bucket_share:      0.239726
single_projection_bucket_share:    0.126712

rows normal_margin <= 0.50:             236
rows normal_margin <= 1.00:             275
rows normal_margin <= 2.00:             292

targeted_trajectory_mean:          0.080304
targeted_trajectory_p90:           0.124239
targeted_first_action_mean:        0.090040

projection_l2_p50:                 1.409488
projection_l2_p90:                 2.528398
half_width_delta_abs_p90:          0.570164

projected scenario labels:
  unavoidable: 292

mechanism_gate_pass: true
outcome_gate_admitted: true
actor_contract_changed: false
training_or_promotion_performed: false
```

M516 passes the M515 mechanism proof gate:

```text
pair_count >= 240
probe_seed_count >= 6
target_count >= 2
config_count >= 2
projected_obstacle_bucket_count >= 8
projection_bucket_count >= 8
single_seed_share <= 0.50
single_config_share <= 0.70
single_target_share <= 0.70
single_obstacle_bucket_share <= 0.35
single_projection_bucket_share <= 0.35
rows <= 0.50 margin >= 40
rows <= 1.00 margin >= 100
trajectory mean >= 0.04
trajectory p90 >= 0.08
```

The selected rows are still all `unavoidable`. This is expected after M514 and
is not a failure of the mechanism gate. Scenario-label diversity remains a
separate scenario-distribution gate, not a mechanism proof admission criterion.

## Interpretation

M516 confirms that the M514 projected rows can support a source/geometry-diverse
terminal-boundary mechanism proof surface once label diversity is separated from
mechanism proof.

The result does not yet prove deployable history-based self-identification. It
only admits the next projection-aware outcome gate. The next gate must replay
the M516 selected rows while preserving the relocated obstacle geometry; using
the existing tail-aligned gate unchanged would reconstruct the original
obstacle positions and invalidate the projection proof.

## Decision

```text
boundary_mechanism_projection_gate_pass_admit_m517_projection_aware_outcome_gate_design
```

Failure classification:

```text
none
```

Next blocker:

```text
m517-projection-aware-boundary-outcome-gate-design
```
