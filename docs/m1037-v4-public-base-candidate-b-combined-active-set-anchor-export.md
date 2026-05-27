# M1037 V4 Public Base Candidate B Combined Active-Set Anchor Export

## Purpose

M1037 implements the no-update combined active-set anchor export designed in
M1036.

It does not run repair, PPO, training, private holdout, promotion, first replay,
or actor-input changes.

## Command

```bash
rm -rf runs/m1037_candidate_b_combined_active_set_anchor_export && \
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.candidate_b_combined_active_set_anchor_export \
  --run-dir runs/m1037_candidate_b_combined_active_set_anchor_export
```

## Inputs

M267/M264 rejected-history trajectory anchor:

```text
runs/m293_current_family_rejected_history_ppo_repair_design/m267_failed_rows_extra4_anchor.npz
```

M183/M170 row16 normal-branch trajectory anchor:

```text
runs/m1034_candidate_b_m183_row16_active_set_anchor_export/m183_row16_normal_trajectory_anchor.npz
```

## Output Artifacts

```text
runs/m1037_candidate_b_combined_active_set_anchor_export/combined_active_set_anchor_balanced.npz
runs/m1037_candidate_b_combined_active_set_anchor_export/combined_active_set_anchor_row16x4.npz
runs/m1037_candidate_b_combined_active_set_anchor_export/combined_active_set_anchor_row16x8.npz
runs/m1037_candidate_b_combined_active_set_anchor_export/combined_active_set_anchor_summary.csv
runs/m1037_candidate_b_combined_active_set_anchor_export/summary.json
```

## Result

M1037 passes:

```text
result_class: candidate_b_combined_active_set_anchor_export_pass
variant_count: 3
combined_rows_expected: 3957
all_variants_loadable: true
all_source_namespaced: true
all_family_weights_match: true
all_row_counts_match: true
actor_inputs_changed: false
repair_used: false
ppo_used: false
checkpoint_promoted: false
private_holdout_used: false
```

## Variant Summary

| Variant | Rows | M267 rows | M183 rows | M267 family sum | M183 family sum | Source collision |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `balanced` | 3957 | 3900 | 57 | 1.00000002 | 1.00000001 | false |
| `row16x4` | 3957 | 3900 | 57 | 1.00000002 | 4.00000003 | false |
| `row16x8` | 3957 | 3900 | 57 | 1.00000002 | 8.00000006 | false |

All variants keep M293 source ids unchanged and offset M1034 source ids by:

```text
1000000
```

Observed source ranges:

```text
M293: 0..300064
M1034 after offset: 1000000..1000000
```

## Interpretation

M1037 resolves the two implementation blockers identified by M1036:

```text
source_index collision: resolved by namespacing M1034 sources at 1000000+
family weight dilution: resolved by family-normalized variants
```

The `row16x4` variant is the primary next repair input because it keeps M267
trajectory retention active while giving the M183/M170 row16 normal branch
enough weight to behave like a hard active-set term.

## Next Route

The next milestone should run a no-PPO exact repair/projection probe using:

```text
runs/m1037_candidate_b_combined_active_set_anchor_export/combined_active_set_anchor_row16x4.npz
```

The gate order remains:

```text
1. P0 actor-input contract unchanged
2. M297/M270 exact no-regression
3. combined active-set anchor sanity
4. M997 temporal exact retention before replay
5. M267/M264 first replay row15 retained
6. M183/M170 first replay row16 retained
```

If the row16x4 repair endpoint still violates M997 temporal retention, the
route should mirror M1031: temporal-safe projection before any first replay.

## Decision

```text
candidate_b_combined_active_set_anchor_export_pass_route_to_repair_projection_probe
```
