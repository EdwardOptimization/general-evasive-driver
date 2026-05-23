# M437 Active-Boundary Residual Implementation

M437 implements the active-boundary residual designed in M436. It is an
infrastructure milestone: no PPO was run, no checkpoint was promoted, and the
deployable actor input/output contract was unchanged.

## Implementation

New module:

```text
src/autodrift/active_boundary_residual.py
```

The exporter reads old-key targeted replay `guard_results.csv` files from the
M434 selective-radius probes and writes a compact corpus:

```text
runs/m437_active_boundary_residual/active_boundary_corpus.npz
runs/m437_active_boundary_residual/active_boundary_rows.csv
runs/m437_active_boundary_residual/summary.json
```

Each row stores:

```text
observation
normal_hidden
wrong_hidden
proof_normal_action
proof_wrong_action
candidate_normal_action
candidate_wrong_action
normal_margin
wrong_history_margin
margin_gap
violation_type
weight
row_id
profile_index
```

The active-boundary residual is training-only. Replay labels, margins,
violation types, proof actions, and candidate actions are not actor inputs.

## Export Result

Command:

```bash
PYTHONPATH=src python -m autodrift.active_boundary_residual \
  --proof-policy m434_r0010=runs/m434_selective_10004_projection_r0010/candidate_checkpoint.pt \
  --candidate-policy m434_r0015=runs/m434_selective_10004_projection_r0015/candidate_checkpoint.pt \
  --candidate-policy m434_r0020=runs/m434_selective_10004_projection_r0020/candidate_checkpoint.pt \
  --candidate-policy m434_tail_r0010=runs/m434_selective_10004_projection_tail_r0010/candidate_checkpoint.pt \
  --guard-results-csv m434_r0015=runs/m434_r0015_old_key_targeted_replay/guard_results.csv \
  --guard-results-csv m434_r0020=runs/m434_r0020_old_key_targeted_replay/guard_results.csv \
  --guard-results-csv m434_tail_r0010=runs/m434_tail_r0010_old_key_targeted_replay/guard_results.csv \
  --reference-manifest runs/m341_old_key_neighborhood_block_a_seed9860/manifest.json \
  --device cpu \
  --run-dir runs/m437_active_boundary_residual
```

Result:

| Metric | Value |
| --- | ---: |
| rows | 6 |
| active cases | 3 |
| wrong-history-safe rows | 3 |
| gap-erosion rows | 3 |
| normal-collision rows | 0 |

Active cases:

```text
10004|perturbed|31|31|9.500000|-1.000000|0.800000
10023|perturbed|12|12|11.000000|-0.800000|1.200000
9998|perturbed|25|25|11.000000|-1.000000|1.400000
```

## Exact Repair Integration

`intervention_objectives.py` now includes `ActiveBoundarySnippets` and a strict
loader for the corpus.

`exact_post_ppo_repair.py` now supports:

```text
--active-boundary-npz
--lambda-active-boundary
--active-boundary-logprob-margin
```

The exact terms are:

```text
active_boundary_loss
active_boundary_wrong_loss
active_boundary_gap_loss
active_boundary_normal_loss
```

Wrong-history-safe rows penalize the candidate wrong-history action becoming
more likely than the proof wrong-history action. Gap-erosion rows also preserve
branch separation between normal and wrong hidden states. Normal-collision rows
use a local normal-branch action anchor, but none appeared in the M437 export.

## No-Update Smoke

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.exact_post_ppo_repair \
  --base-checkpoint runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --raw-checkpoint runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --preference-npz runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz \
  --outcome-npz runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz \
  --old-key-preference-npz runs/m377_cumulative_gap_tail_v2_old_key_preference_corpus/old_key_preference_corpus.npz \
  --old-key-recovery-npz runs/m398_old_key_normal_margin_recovery_targets/old_key_recovery_corpus.npz \
  --current-family-conflict-npz runs/m393_current_family_rejected_boundary_targets/current_family_conflict_corpus.npz \
  --active-boundary-npz runs/m437_active_boundary_residual/active_boundary_corpus.npz \
  --start-mode repair_from_raw \
  --steps 0 \
  --lambda-active-boundary 1000000000 \
  --device cpu \
  --run-dir runs/m437_active_boundary_no_update_smoke
```

Result:

| Metric | Value |
| --- | ---: |
| active boundary rows | 6 |
| active_boundary_loss | 0.0010130878 |
| active_boundary_wrong_loss | 0.0005824607 |
| active_boundary_gap_loss | 0.0004306272 |
| active_boundary_normal_loss | 0.0 |
| exact M297 delta vs base | 0.0 |
| exact M270 delta vs base | 0.0 |
| old-key surrogate delta vs base | 0.0 |
| exact lexicographic pass | true |

## Tests

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_active_boundary_residual.py \
  tests/test_exact_post_ppo_repair.py
```

Result:

```text
21 passed in 2.18s
```

Compile check:

```bash
python -m compileall -q src tests
```

Result: passed.

## Decision

M437 passes its infrastructure gate. The active-boundary residual can represent
both `10004`/`9998` wrong-history safety failures and `10023` gap erosion, can
be loaded by exact repair, and passes a no-update smoke without actor-contract
changes.

Admit:

```text
m438-active-boundary-projection-probe
```

M438 should run a no-PPO projection probe. It should test whether adding this
active-boundary residual can recover more M406 utility than M434 `r0010`
(`0.103529`) while preserving exact objectives, M267/M264 `17/17`, old-key
compact `40/40`, and M183/M170 `17/17`.
