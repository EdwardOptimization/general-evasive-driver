# M441 Active-Boundary V2 Residual Implementation

M441 implements the active-boundary v2 residual designed in M440. It is an
infrastructure milestone: no projection, no PPO, no checkpoint promotion, no
threshold changes, and no actor input/output changes.

## Implementation

New module:

```text
src/autodrift/active_boundary_v2_residual.py
```

New exact-repair integration:

```text
--active-boundary-v2-npz
--lambda-active-boundary-v2
--active-boundary-v2-logprob-margin
```

New loader/dataclass:

```text
ActiveBoundaryV2Snippets
load_active_boundary_v2_snippets
```

New exact terms:

```text
active_boundary_v2_loss
active_boundary_v2_wrong_loss
active_boundary_v2_gap_loss
active_boundary_v2_normal_loss
```

The v2 residual is training-only. Margins, violation types, active-case labels,
and proof/candidate actions are not deployable actor inputs.

## Corpus Export

Command:

```bash
PYTHONPATH=src python -m autodrift.active_boundary_v2_residual \
  --proof-policy m434_r0010=runs/m434_selective_10004_projection_r0010/candidate_checkpoint.pt \
  --candidate-policy m438_r0015_lactive1e12=runs/m438_r0015_active_boundary_lactive1e12_s40_seed10161/candidate_checkpoint.pt \
  --candidate-policy m438_tail_lactive1e12=runs/m438_tail_r0010_active_boundary_lactive1e12_s40_seed10159/candidate_checkpoint.pt \
  --candidate-policy m438_tail_lactive1e14=runs/m438_tail_r0010_active_boundary_lactive1e14_s40_seed10160/candidate_checkpoint.pt \
  --guard-results-csv m438_r0015_lactive1e12=runs/m438_r0015_lactive1e12_old_key_targeted_replay/guard_results.csv \
  --guard-results-csv m438_tail_lactive1e12=runs/m438_tail_lactive1e12_old_key_targeted_replay/guard_results.csv \
  --guard-results-csv m438_tail_lactive1e14=runs/m438_tail_lactive1e14_old_key_targeted_replay/guard_results.csv \
  --reference-manifest runs/m341_old_key_neighborhood_block_a_seed9860/manifest.json \
  --device cpu \
  --run-dir runs/m441_active_boundary_v2_residual
```

Artifacts:

```text
runs/m441_active_boundary_v2_residual/active_boundary_v2_corpus.npz
runs/m441_active_boundary_v2_residual/active_boundary_v2_rows.csv
runs/m441_active_boundary_v2_residual/summary.json
```

Export result:

| Metric | Value |
| --- | ---: |
| base active rows | 9 |
| exported window rows | 36 |
| active cases | 3 |
| window offsets | `[-6, -4, -2, 0]` |
| wrong-history-safe rows | 16 |
| gap-erosion rows | 12 |
| normal-collision rows | 8 |

Active cases:

```text
10004|perturbed|31|31|9.500000|-1.000000|0.800000
10023|perturbed|12|12|11.000000|-0.800000|1.200000
9998|perturbed|25|25|11.000000|-1.000000|1.400000
```

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
  --active-boundary-v2-npz runs/m441_active_boundary_v2_residual/active_boundary_v2_corpus.npz \
  --start-mode repair_from_raw \
  --steps 0 \
  --lambda-active-boundary-v2 1000000000000 \
  --device cpu \
  --run-dir runs/m441_active_boundary_v2_no_update_smoke
```

Result:

| Metric | Value |
| --- | ---: |
| active-boundary-v2 rows | 36 |
| active_boundary_v2_loss | 0.0059865140 |
| active_boundary_v2_wrong_loss | 0.0042643221 |
| active_boundary_v2_gap_loss | 0.0017221756 |
| active_boundary_v2_normal_loss | 0.0000000165 |
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
23 passed in 1.06s
```

Compile check:

```bash
python -m compileall -q src tests
```

Result: passed.

## Decision

M441 passes its infrastructure gate. V2 now has a compact trajectory-window
corpus, loader, exact terms, focused tests, and a no-update exact repair smoke.

Admit:

```text
m442-active-boundary-v2-projection-probe
```

M442 should run the first no-PPO projection probe with v2. It should start from
the M438 conditions and test whether v2 can make a looser profile proof-safe
while beating M438 `r0015` recovery retained vs M406 (`0.120957`).
