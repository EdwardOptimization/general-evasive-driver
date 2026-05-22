# M164 Boundary-Outcome Replay Gate

M163 passed fixed objective, behavior, and protected-key gates, but objective
loss alone does not prove that the update changes actual continuation outcomes.
M164 replays the exact M162 boundary rows under M156 and M163.

This gate does not re-mine an easier surface. It uses:

```text
runs/m162_m156_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv
```

The actor input contract is unchanged. M162 row ids, target ids, group ids,
geometry keys, and outcome labels are replay selection metadata only.

## Implementation

Added:

```text
src/autodrift/boundary_outcome_replay_gate.py
tests/test_boundary_outcome_replay_gate.py
```

The replay gate:

1. loads fixed M162 boundary corpus rows;
2. reconstructs each policy's recurrent left/right snapshots from seed/step;
3. relocates the obstacle to the stored boundary geometry;
4. rolls out normal history and wrong matched history;
5. compares M156 baseline versus M163 candidate on the same row ids.

## Command

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.boundary_outcome_replay_gate \
  --checkpoint-policy m156_s20=runs/m156_capability_belief_aux_s20_seed9630/optimized_checkpoint.pt \
  --checkpoint-policy m163_a100_s20=runs/m163_boundary_outcome_actor_coupling_anchor100_s20_seed9832/optimized_checkpoint.pt \
  --corpus-csv runs/m162_m156_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --max-continuation-steps 60 \
  --baseline-policy m156_s20 \
  --candidate-policy m163_a100_s20 \
  --max-normal-success-drop 0.0 \
  --max-normal-margin-regression 0.005 \
  --max-margin-gap-regression 0.001 \
  --max-success-drop-count-regression 0 \
  --device cpu \
  --run-dir runs/m164_boundary_outcome_replay_gate_seed9510
```

## Result

Run:

```text
runs/m164_boundary_outcome_replay_gate_seed9510
```

Aggregate comparison:

| Metric | M156 | M163 | Delta |
| --- | ---: | ---: | ---: |
| rows | 88 | 88 | 0 |
| normal success rate | 0.681818 | 0.681818 | 0.000000 |
| wrong-history success rate | 0.568182 | 0.500000 | -0.068182 |
| success-drop count | 10 | 16 | +6 |
| normal margin mean | 0.019475 | 0.017946 | -0.001529 |
| margin gap mean | -0.003344 | -0.001989 | +0.001355 |

Gate checks:

| Gate | Pass |
| --- | --- |
| normal success retention | true |
| normal margin retention | true |
| wrong-history gap retention | true |
| success-drop count retention | true |

Target detail:

| Policy | Target | Rows | Normal success | Wrong success | Success drops | Margin gap mean |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| m156_s20 | future braking deceleration | 44 | 0.477273 | 0.409091 | 3 | -0.012154 |
| m163_a100_s20 | future braking deceleration | 44 | 0.477273 | 0.340909 | 6 | -0.009012 |
| m156_s20 | future lateral accel response | 37 | 0.864865 | 0.729730 | 5 | 0.005602 |
| m163_a100_s20 | future lateral accel response | 37 | 0.864865 | 0.648649 | 8 | 0.005072 |
| m156_s20 | future yaw response | 7 | 1.000000 | 0.714286 | 2 | 0.004745 |
| m163_a100_s20 | future yaw response | 7 | 1.000000 | 0.714286 | 2 | 0.004828 |

M163 does not improve every per-target margin metric, but the aggregate fixed
surface passes the pre-registered retention thresholds. It preserves normal
success, keeps normal-margin regression within tolerance, and increases the
number of wrong-history-induced failures.

## Decision

M164 is positive.

M163 is now more than a fixed-logprob objective candidate: on the exact M162
boundary replay surface, it preserves normal-history success and makes wrong
matched history more outcome-damaging.

Decision: admit a guarded PPO smoke design from M163. Do not run large PPO or
claim driver-like self-identification yet.

The next PPO smoke must remain constrained:

- initialize from M163;
- use M156/M163 behavior retention as hard gates;
- keep M162/M164 boundary replay as a post-update gate;
- include protected critical-key replay;
- reject the PPO continuation if it weakens normal boundary outcomes or erases
  the wrong-history degradation signal.

## Validation

```text
python -m compileall -q src tests
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_boundary_outcome_replay_gate.py
```

Result:

```text
4 passed
```
