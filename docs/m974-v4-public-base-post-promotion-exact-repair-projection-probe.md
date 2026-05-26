# M974 V4 Public Base Post-Promotion Exact Repair Projection Probe

## Purpose

M974 tests the M973 design: can the rejected M972 raw PPO proposal be handled
by no-PPO exact full-corpus repair/projection before replay gates?

M974 does not run PPO, promote a checkpoint, use private holdout, or change
actor inputs.

## Inputs

Base checkpoint:

```text
runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_1_0.pt
```

M972 raw PPO proposal:

```text
runs/ppo_m972_post_promotion_guarded_smoke_seed5972/checkpoint.pt
```

Exact corpora:

```text
runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz
runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz
runs/m293_current_family_rejected_history_ppo_repair_design/m267_failed_rows_extra4_anchor.npz
```

## Exact Repair Candidates

Three candidates were generated with `python -m autodrift.exact_post_ppo_repair`.

| Candidate | Start mode | Checkpoint | Exact M297 delta | Exact M270 delta | Exact pass |
| --- | --- | --- | ---: | ---: | --- |
| raw_s40 | repair_from_raw | `runs/m974_exact_repair_from_raw_s40_seed5973/candidate_checkpoint.pt` | -0.000009298 | -0.000033319 | true |
| base_s40 | repair_from_base | `runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt` | -0.000044584 | -0.000060797 | true |
| line_boundary_s40 | line_search_boundary | `runs/m974_exact_repair_line_boundary_s40_seed5975/candidate_checkpoint.pt` | -0.000044584 | -0.000060797 | true |

The line-search audit shows that direct interpolation from alpha `1.0` toward
M972 raw has no exact-safe positive alpha under the strict `1e-7` tolerance:
`alpha=0` passes and `alpha=0.001` already fails exact no-regression. Repair is
therefore necessary; interpolation alone is not a safe acceptance mechanism.

## First Replay Gates

The raw-start repair partially recovers M972's proof washout but does not fully
restore M267/M264:

```text
M972 raw PPO M267/M264 success-drop: 15 / 17
M974 raw-start repair M267/M264 success-drop: 16 / 17
```

The remaining raw-start failure is row `15`:

```text
target: future_braking_deceleration
pair: 9530:21:9550:21
wrong_history_margin: +0.00012114673385488217
wrong_history_success: true
```

The base-start candidate passes first replay gates and is selected for the next
full public-gate design.

Selected candidate:

```text
runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
```

### M267/M264 First Replay

Run dir:

```text
runs/m974_base_s40_m267_m264_first_replay
```

| Metric | Value |
| --- | ---: |
| Rows | 17 |
| Baseline success-drop count | 17 |
| Candidate success-drop count | 17 |
| Normal success delta | 0.0 |
| Wrong-history success delta | 0.0 |
| Normal margin mean delta | +0.000031 |
| Margin gap mean delta | +0.000025 |
| Gate pass | true |

### M183/M170 First Replay

Run dir:

```text
runs/m974_base_s40_m183_m170_first_replay
```

| Metric | Value |
| --- | ---: |
| Rows | 17 |
| Baseline success-drop count | 17 |
| Candidate success-drop count | 17 |
| Normal success delta | 0.0 |
| Wrong-history success delta | 0.0 |
| Normal margin mean delta | +0.000033 |
| Margin gap mean delta | +0.000030 |
| Gate pass | true |

## Interpretation

M974 is a qualified positive:

- M972 raw PPO movement is not directly acceptable.
- Raw-start exact repair retains some proposal value but still leaves row `15`
  wrong-history-safe.
- Base-start exact repair creates a small proof-safe improvement from the
  alpha `1.0` base.
- The selected base-start candidate passes exact M297/M270 and first replay
  gates.

This does not yet justify promotion. Only two first replay gates were run, and
fresh generalization/behavior gates were not rerun for the repaired candidate.

## Decision

Route to full public-gate design:

```text
m975-v4-public-base-post-promotion-exact-repair-full-public-gate-design
```

Decision:

```text
exact_repair_projection_first_replay_pass_route_to_full_public_gate_design
```

## Artifacts

```text
runs/m974_exact_repair_from_raw_s40_seed5973/summary.json
runs/m974_exact_repair_from_base_s40_seed5974/summary.json
runs/m974_exact_repair_line_boundary_s40_seed5975/summary.json
runs/m974_raw_s40_m267_m264_first_replay/summary.json
runs/m974_base_s40_m267_m264_first_replay/summary.json
runs/m974_base_s40_m183_m170_first_replay/summary.json
```
