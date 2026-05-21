# M115 Wrong-History Boundary Relocation Surface

M114 found near-boundary outcome rows for `reset_hidden` and
`zero_current_response`, but it still found zero `wrong_matched_history` rows.
M115 tests whether the blocker is that the passive M113 continuations are not
close enough to the collision boundary for the smaller wrong-history trajectory
differences to matter.

## Implementation

Added:

```text
src/autodrift/wrong_history_boundary_relocation_surface.py
tests/test_wrong_history_boundary_relocation_surface.py
```

The harness consumes M113 `outcome_interventions.csv`, selects
`wrong_matched_history` candidate rows, reconstructs the original M111/M113
snapshots, deep-copies the snapshot env, and tightens the obstacle half-width at
the current ego-frame obstacle location.

For each relocated snapshot it replays:

```text
normal
wrong_matched_history
reset_hidden
zero_current_response
zero_action_history
delayed_history
```

Acceptance for wrong-history rows requires:

```text
normal_success == true
0.0 <= normal_margin <= 0.20
and either:
  wrong history success_drop == true
  or normal_margin - wrong_margin >= min_margin_gap
```

The actor input contract is unchanged. The relocation is a gate-time scenario
construction; it does not add hidden parameters or oracle labels to the actor.

## Focused Validation

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
  python -m pytest -q tests/test_wrong_history_boundary_relocation_surface.py

python -m compileall -q src tests
```

Result:

```text
5 passed
compileall passed
```

## Smoke

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.wrong_history_boundary_relocation_surface \
  --checkpoint-policy m102=runs/m102_retention_actor_coupling_seed9550/optimized_checkpoint.pt \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --outcome-csv runs/m113_matched_history_outcome_gate_seed9510/outcome_interventions.csv \
  --delay-steps 10 \
  --max-continuation-steps 60 \
  --max-pairs-per-checkpoint-target 1 \
  --min-base-action-distance 0.02 \
  --target-normal-margins 0.005,0.02,0.05 \
  --half-width-inflations 0 \
  --min-margin-gap 0.005 \
  --min-accepted-wrong-rows 1 \
  --report-variants wrong_matched_history \
  --device cpu \
  --run-dir runs/m115_wrong_history_boundary_relocation_smoke_seed9510
```

Result:

```text
candidate_count: 9
row_count: 12
accepted_wrong_history_rows: 12
accepted_wrong_history_pairs: 3
wrong_history_success_drop_count: 3
surface_found: true
```

The smoke exposed one real implementation edge case: some M113 candidate
snapshots already had the obstacle behind the ego frame. The harness now skips
those rows unless explicit positive relocation distances are provided.

## Formal Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.wrong_history_boundary_relocation_surface \
  --checkpoint-policy m62=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --checkpoint-policy m102=runs/m102_retention_actor_coupling_seed9550/optimized_checkpoint.pt \
  --checkpoint-policy m105=runs/m105_anchor10_outcome_coupling_smoke_seed9710/optimized_checkpoint.pt \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --outcome-csv runs/m113_matched_history_outcome_gate_seed9510/outcome_interventions.csv \
  --delay-steps 10 \
  --max-continuation-steps 60 \
  --max-pairs-per-checkpoint-target 10 \
  --min-base-action-distance 0.02 \
  --target-normal-margins 0.005,0.01,0.02,0.05,0.10,0.15 \
  --half-width-inflations 0 \
  --min-margin-gap 0.02 \
  --min-accepted-wrong-rows 10 \
  --report-variants wrong_matched_history,reset_hidden,zero_current_response,zero_action_history,delayed_history \
  --device cpu \
  --run-dir runs/m115_wrong_history_boundary_relocation_surface_seed9510
```

Artifacts:

```text
runs/m115_wrong_history_boundary_relocation_surface_seed9510/summary.json
runs/m115_wrong_history_boundary_relocation_surface_seed9510/boundary_relocation_rows.csv
runs/m115_wrong_history_boundary_relocation_surface_seed9510/accepted_wrong_history_rows.csv
runs/m115_wrong_history_boundary_relocation_surface_seed9510/surface_summary.csv
```

## Formal Result

Aggregate:

| Metric | Value |
| --- | ---: |
| Candidate rows | 90 |
| Relocation replay rows | 3045 |
| Accepted wrong-history rows | 12 |
| Accepted wrong-history source pairs | 11 |
| Wrong-history success drops | 12 |
| Accepted reset rows | 275 |
| Accepted zero-current rows | 332 |
| Surface found | true |

Wrong-history rows by checkpoint:

| Checkpoint | Accepted wrong-history rows | Accepted pairs |
| --- | ---: | ---: |
| M62 | 0 | 0 |
| M102 | 6 | 6 |
| M105 | 6 | 5 |

Accepted wrong-history rows are distributed across braking, lateral, and yaw
targets:

| Checkpoint | Target | Rows | Mean normal margin | Mean gap |
| --- | --- | ---: | ---: | ---: |
| M102 | braking | 2 | 0.006516 | 0.007984 |
| M102 | lateral | 3 | 0.006586 | 0.007642 |
| M102 | yaw | 1 | 0.006334 | 0.007158 |
| M105 | braking | 2 | 0.006335 | 0.007475 |
| M105 | lateral | 3 | 0.006380 | 0.007164 |
| M105 | yaw | 1 | 0.006243 | 0.006777 |

The accepted rows are all success-drop rows:

```text
normal history: obstacle_completed, positive margin about 0.006 m
wrong history: collision, slightly negative margin
```

The largest wrong-history margin gap is only `0.008819`, so these rows pass by
crossing a tight boundary, not by showing a broad clearance-margin advantage.

No-relocation control:

| Variant | Original rows | Accepted original rows | Success drops | Max gap |
| --- | ---: | ---: | ---: | ---: |
| wrong_matched_history | 87 | 0 | 0 | 0.007461 |
| reset_hidden | 87 | 31 | 0 | 0.035691 |
| zero_current_response | 87 | 45 | 0 | 0.061959 |

This confirms the M114/M113 diagnosis: passive rows do not make wrong-history
outcome-critical. Boundary tightening is required to expose the wrong-history
success-drop surface.

## Interpretation

M115 is a positive construction gate, not a final self-identification proof.

What it proves:

- there exists a boundary-tightened M111/M113 matched surface where normal
  history succeeds and wrong matched history collides;
- the signal is not present without relocation;
- reset and zero-current remain much stronger degradation modes and must be
  reported separately.

What it does not prove:

- broad wrong-history margin loss;
- robustness across independent M111/M113 probe seeds;
- that a trained objective will generalize from these narrow boundary rows;
- that M62 already has the behavior, since M62 produces zero accepted
  wrong-history rows in this gate.

## Decision

Proceed, but do not train from M115 directly as if it were a paper-grade
self-identification surface. The next step should verify the constructed
surface with a split/robustness gate before using it as a training objective.

Next task: M116 should test whether the M115 boundary-tightened wrong-history
surface survives held-out candidate selection, non-duplicated source pairs,
and stricter dominance checks, then decide whether to create a
wrong-history-boundary objective.
