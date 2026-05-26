# M1036 V4 Public Base Candidate B Combined Active-Set Repair Design

## Purpose

M1036 designs the next branch after M1035 synthesized the Candidate B guarded
PPO readiness work.

M1036 is design only. It does not run repair, PPO, training, private holdout,
promotion, first replay, or actor-input changes.

## Parent State

Current public-gate base:

```text
runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt
```

Raw PPO proposal:

```text
runs/ppo_m1026_candidate_b_guarded_smoke_seed61026/checkpoint.pt
```

M1035 closed the `v4_public_base_candidate_b_guarded_ppo_readiness` branch and
opened:

```text
candidate_b_combined_active_set_repair
```

The active-set evidence to preserve is:

```text
M997 temporal exact retention
M297/M270 exact no-regression
M267/M264 row15 rejected-history failure retention
M183/M170 row16 normal branch retention
P0 actor-input contract unchanged
```

## Required Data

M1036 inspected the two trajectory anchors needed for combined retention:

| Source | Rows | Sources | Source range | Weight sum |
| --- | ---: | ---: | --- | ---: |
| M293 rejected-history trajectory anchor | 3900 | 48 | 0..300064 | 106426.71 |
| M1034 M183/M170 row16 normal anchor | 57 | 1 | 0..0 | 570.00 |

Both anchors use the same `TrajectoryActionAnchor` schema:

```text
observation
hidden
reference_action
source_index
step_index
weight
```

Their tensor shapes are compatible:

```text
M293:
  observation 3900 x 72
  hidden 3900 x 128
  reference_action 3900 x 3

M1034:
  observation 57 x 72
  hidden 57 x 128
  reference_action 57 x 3
```

So a combined anchor is feasible, but a naive concat is not acceptable.

## Why Direct Concatenation Is Not Enough

There are two concrete problems:

```text
source_index collision:
  M293 uses source_index 0 and M1034 also uses source_index 0.

family weight dilution:
  M293 has 3900 rows and weight sum 106426.71.
  M1034 has 57 rows and weight sum 570.00.
```

If these are concatenated without normalization, the M183/M170 row16 normal
branch can be underweighted in the aggregate trajectory-anchor loss. That would
repeat the M1031 failure mode: M267/M264 row15 can be retained while M183/M170
row16 crosses the terminal margin boundary.

## Design Decision

M1037 should not run repair yet. It should first materialize a combined
active-set trajectory anchor with explicit source namespacing and family-level
weight normalization.

This is a separate evidence step because the optimizer can only use one
`--replay-trajectory-anchor-npz` path today. The combined anchor must therefore
carry the active-set priority in its rows, source ids, and weights before
`exact_post_ppo_repair` sees it.

## M1037 Combined Anchor Export

M1037 should implement:

```text
autodrift.candidate_b_combined_active_set_anchor_export
```

Inputs:

```text
--m267-rejected-anchor-npz runs/m293_current_family_rejected_history_ppo_repair_design/m267_failed_rows_extra4_anchor.npz
--m183-row16-normal-anchor-npz runs/m1034_candidate_b_m183_row16_active_set_anchor_export/m183_row16_normal_trajectory_anchor.npz
--run-dir runs/m1037_candidate_b_combined_active_set_anchor_export
```

Outputs:

```text
runs/m1037_candidate_b_combined_active_set_anchor_export/combined_active_set_anchor_balanced.npz
runs/m1037_candidate_b_combined_active_set_anchor_export/combined_active_set_anchor_row16x4.npz
runs/m1037_candidate_b_combined_active_set_anchor_export/combined_active_set_anchor_row16x8.npz
runs/m1037_candidate_b_combined_active_set_anchor_export/combined_active_set_anchor_summary.csv
runs/m1037_candidate_b_combined_active_set_anchor_export/summary.json
```

The export should create three anchor variants:

| Variant | M293 family total | M1034 row16 family total | Purpose |
| --- | ---: | ---: | --- |
| `balanced` | 1.0 | 1.0 | baseline combined anchor |
| `row16x4` | 1.0 | 4.0 | primary hard-active-set candidate |
| `row16x8` | 1.0 | 8.0 | diagnostic if row16 remains weak |

The row-level weights should preserve each source's internal relative weights,
then normalize by family:

```text
normalized_weight_i =
  original_weight_i / sum(original_weight within family) * family_total
```

This makes `lambda_replay_trajectory_anchor` interpretable and prevents one
family from silently dominating due to row count.

## Source Namespacing

M1037 should offset M1034 source ids so `exact_trajectory_action_anchor_loss_by_source`
can still diagnose hard losses by source without collision:

```text
M293 source_index: preserve original source_index
M1034 source_index: 1000000 + original source_index
```

The NPZ may include diagnostic extra arrays ignored by the current loader:

```text
family_id
family_weight_total
source_label_id
```

But the required loader-visible fields must remain exactly compatible with
`load_trajectory_action_anchor`.

## No-Update Sanity Gates For M1037

M1037 must verify:

```text
all variants load with load_trajectory_action_anchor
rows = 3900 + 57 = 3957
observation shape = 3957 x 72
hidden shape = 3957 x 128
reference_action shape = 3957 x 3
M1034 source indices are offset and do not collide with M293
family weight sums match the declared variant totals
all weights are positive and finite
P0 actor inputs unchanged
ppo_used = false
repair_used = false
checkpoint_promoted = false
private_holdout_used = false
```

M1037 should not evaluate private holdout and should not run first replay. It is
only an anchor materialization and exact-load sanity milestone.

## M1038 Repair/Projection Plan

If M1037 passes, M1038 should run no-PPO exact repair/projection using the
combined anchor. The initial candidate family should be:

| Candidate | Start mode | Combined anchor |
| --- | --- | --- |
| `base_row16x4_s40` | `repair_from_base` | `row16x4` |
| `raw_row16x4_s40` | `repair_from_raw` | `row16x4` |
| `line_row16x4_s40` | `line_search_boundary` | `row16x4` |

Use `balanced` and `row16x8` only as diagnostic fallbacks if the primary
`row16x4` family is too weak or too restrictive.

Suggested defaults:

```text
steps: 40
learning_rate: 3e-6
train_scope: actor_coupling
train_log_std: false
selection_policy: best_feasible
lambda_m297: 1000000
lambda_m270: 1000000
lambda_current_family_conflict: 1000
lambda_current_family_conflict_rejected: 10
lambda_replay_trajectory_anchor: 10
lambda_action_anchor: 100
lambda_param_base: 1
lambda_param_raw: 0.02 for raw-start only, otherwise 0
```

Required inputs:

```text
M297 preference:
  runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz

M270 outcome intervention:
  runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz

M393 row15 conflict:
  runs/m393_current_family_rejected_boundary_targets/current_family_conflict_corpus.npz

Combined active-set anchor:
  runs/m1037_candidate_b_combined_active_set_anchor_export/combined_active_set_anchor_row16x4.npz
```

M1038 should save repair endpoints but must still gate them through temporal
projection before replay. The M1029 lesson remains active: exact M297/M270
repair endpoints can violate M997 temporal retention.

## Gate Order For M1038+

The next optimizer/projection milestone must use this order:

1. P0 actor-input contract unchanged.
2. M297/M270 exact no-regression versus Candidate B.
3. Combined active-set anchor exact sanity:

```text
M293 family trajectory loss does not exceed Candidate B by tolerance.
M1034 family trajectory loss does not exceed Candidate B by tolerance.
```

4. M997 temporal exact retention before replay.
5. Nontrivial movement retained:

```text
alpha >= 0.05
or M297 delta <= -0.00005
or M270 delta <= -0.000002
```

6. M267/M264 first replay passes `17/17`, including row15 wrong-history failure.
7. M183/M170 first replay passes `17/17`, including row16 normal success.
8. Only then route to a full public proof/generalization/behavior gate design.

## Result Classes For Later Implementation

Use these classifications:

```text
candidate_b_combined_active_set_anchor_export_pass:
  M1037 exports loadable family-normalized combined anchors.

candidate_b_combined_active_set_anchor_export_invalid:
  anchor shapes, source namespacing, or family weights are invalid.

candidate_b_combined_active_set_repair_temporal_regression:
  repair endpoint satisfies exact/anchor objectives but fails M997 temporal.

candidate_b_combined_active_set_projection_proof_washout:
  temporal/exact/anchor-safe candidate fails M267/M264 or M183/M170 first replay.

candidate_b_combined_active_set_projection_first_replay_candidate:
  candidate passes M997, exact, active-set, M267/M264, and M183/M170 first replay.
```

## Explicit Non-Goals

M1036 and M1037 must not:

- run PPO;
- run repair optimization;
- promote a checkpoint;
- use private holdout;
- relax M997 thresholds;
- remove M267/M264 row15 constraints;
- remove M183/M170 row16 constraints;
- change actor inputs;
- claim broader scenario-distribution improvement.

## Decision

```text
candidate_b_combined_active_set_repair_design_admit_combined_anchor_export
```

Next milestone:

```text
m1037-v4-public-base-candidate-b-combined-active-set-anchor-export
```
