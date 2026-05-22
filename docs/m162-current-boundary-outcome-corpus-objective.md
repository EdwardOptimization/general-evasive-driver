# M162 Current Boundary-Outcome Corpus Objective

M161 found a current zero-relvel boundary surface where wrong matched history
can change continuation outcomes. M162 converts that surface into reusable
training-time artifacts before any actor update or PPO continuation.

This milestone is objective-only. It does not claim driver-level
self-identification.

## Implementation

Added:

```text
src/autodrift/boundary_outcome_corpus_objective.py
tests/test_boundary_outcome_corpus_objective.py
```

The builder reads M161 `accepted_wrong_history_rows.csv`, reconstructs the
left/right recurrent snapshots from seed/step, relocates the obstacle to the
M161 boundary geometry, and exports:

```text
boundary_outcome_corpus.npz
boundary_outcome_corpus.csv
selected_boundary_rows.csv
corpus_summary.json
objective_summary.json
objective_seed_summary.csv
```

The deployable student input contract is:

```text
observation
preferred_hidden
rejected_hidden
```

The hidden states are generated from the deployable human-view recurrent
history. Relocated outcome labels, score deltas, target ids, and group ids are
training-time metadata only; they are not actor inputs.

An exact geometry dedup was added after the first run showed repeated rows from
different M161 candidate/source ids pointing to the same physical pair and
relocated obstacle geometry. The final corpus has:

```text
max_rows_per_boundary_geometry = 1
```

## M156 Main Corpus

Run:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.boundary_outcome_corpus_objective \
  --checkpoint-policy m156_s20=runs/m156_capability_belief_aux_s20_seed9630/optimized_checkpoint.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --boundary-rows-csv runs/m161_m156_boundary_relocation_zero_relvel_seed9510/accepted_wrong_history_rows.csv \
  --delay-steps 10 \
  --device cpu \
  --max-rows-per-physical-pair 12 \
  --optimization-seeds 9620,9621,9622 \
  --steps 180 \
  --batch-size 64 \
  --learning-rate 0.0003 \
  --weight-decay 0.001 \
  --hidden-dim 96 \
  --run-dir runs/m162_m156_boundary_outcome_corpus_dedup_seed9510
```

Corpus:

| Metric | Value |
| --- | ---: |
| rows | 88 |
| physical pairs | 16 |
| unique boundary geometries | 88 |
| max rows / physical pair | 7 |
| max rows / physical pair fraction | 0.079545 |
| success-drop rows | 18 |
| mean margin gap | 0.008882 |
| max margin gap | 0.019254 |
| mean score delta | 0.213427 |
| action reconstruction error max | 0.0 |

Target counts:

| Target | Rows |
| --- | ---: |
| future braking deceleration | 44 |
| future lateral accel response | 37 |
| future yaw response | 7 |

Objective sanity:

| Metric | Value |
| --- | ---: |
| objective pass | true |
| seed pass count | 3 / 3 |
| mean val combined loss improvement | 1.856069 |
| min val combined loss improvement | 0.744064 |
| mean val delta loss improvement | 1.806001 |
| min val delta loss improvement | 0.578678 |
| mean val pairwise accuracy after | 0.987654 |
| min val pairwise accuracy after | 0.962963 |

Decision for the M156 mainline: admit for guarded actor-update design, not PPO.

## M142 Calibration

Run:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.boundary_outcome_corpus_objective \
  --checkpoint-policy m142_a400=runs/m142_interpolate_m132_to_m139_s20/checkpoints/alpha_0_4.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --boundary-rows-csv runs/m161_m142_boundary_relocation_zero_relvel_seed9510/accepted_wrong_history_rows.csv \
  --delay-steps 10 \
  --device cpu \
  --max-rows-per-physical-pair 12 \
  --optimization-seeds 9620,9621,9622 \
  --steps 180 \
  --batch-size 64 \
  --learning-rate 0.0003 \
  --weight-decay 0.001 \
  --hidden-dim 96 \
  --run-dir runs/m162_m142_boundary_outcome_corpus_dedup_seed9510
```

Corpus:

| Metric | Value |
| --- | ---: |
| rows | 90 |
| physical pairs | 16 |
| unique boundary geometries | 90 |
| max rows / physical pair | 7 |
| max rows / physical pair fraction | 0.077778 |
| success-drop rows | 20 |
| mean margin gap | 0.010484 |
| max margin gap | 0.021691 |
| mean score delta | 0.232706 |
| action reconstruction error max | 0.0 |

Objective sanity:

| Metric | Value |
| --- | ---: |
| objective pass | false |
| seed pass count | 2 / 3 |
| mean val combined loss improvement | 0.158713 |
| min val combined loss improvement | -1.577878 |
| mean val delta loss improvement | 0.184979 |
| min val delta loss improvement | -1.440938 |
| mean val pairwise accuracy after | 0.844017 |
| min val pairwise accuracy after | 0.615385 |

A conservative rerun with learning rate `1e-4` and `300` steps still failed
the strict all-seed objective rule for M142:

```text
runs/m162_m142_boundary_outcome_corpus_dedup_lr1e4_seed9510
objective_pass=false
seed_pass_count=2/3
```

This means the M142 calibration corpus has positive average signal but not a
stable all-split objective pass under the current sanity harness. It should be
kept as a calibration/control artifact, not used to admit an actor update.

## Decision

M162 is a positive M156 mainline objective-sanity milestone:

```text
runs/m162_m156_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.npz
```

is admitted for guarded actor-update design.

Guardrails for the next milestone:

- Use the M162 M156 corpus only as training-time supervision.
- Do not feed M161 labels, hidden parameters, target ids, or geometry keys to
  the deployable actor.
- Start from M156 and use a small guarded actor-coupling update, not PPO.
- Require behavior retention and boundary outcome gates before any PPO
  continuation.
- Keep M142 as a calibration/control surface because its dedup objective sanity
  did not pass the strict all-seed rule.

## Validation

```text
python -m compileall -q src tests
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_boundary_outcome_corpus_objective.py
PYTHONPATH=src python -m autodrift.research_validate
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q
scripts/hooks/pre-commit
```

Result:

```text
targeted: 7 passed
research validation passed (enforce_from_priority=870, enforced_tasks=81)
full pytest: 394 passed, 3 warnings
lightweight pre-commit hook: 16 passed
```
