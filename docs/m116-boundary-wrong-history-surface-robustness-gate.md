# M116 Boundary Wrong-History Surface Robustness Gate

M115 constructed a positive wrong-history boundary surface, but the accepted
rows were narrow. M116 asks whether that surface is robust enough to train a
wrong-history objective.

## Implementation

Added:

```text
src/autodrift/boundary_wrong_history_surface_robustness.py
tests/test_boundary_wrong_history_surface_robustness.py
```

The harness is post-hoc by design. It consumes the M115
`boundary_relocation_rows.csv` and measures whether accepted
`wrong_matched_history` rows survive stricter diversity gates:

```text
physical source pair diversity:
  (left_seed, left_step, right_seed, right_step)

decision-step diversity:
  distinct left_step / right_step

boundary diversity:
  normal_margin_bucket

checkpoint / target diversity:
  checkpoint_label, target

control:
  M62 must remain unadmitted
```

This avoids mistaking duplicated rows across target labels or checkpoints for
independent evidence.

## Focused Validation

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
  python -m pytest -q tests/test_boundary_wrong_history_surface_robustness.py

python -m compileall -q src tests
```

Result:

```text
4 passed
compileall passed
```

## Formal Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.boundary_wrong_history_surface_robustness \
  --boundary-rows-csv runs/m115_wrong_history_boundary_relocation_surface_seed9510/boundary_relocation_rows.csv \
  --control-checkpoint-label m62 \
  --margin-bucket-width 0.01 \
  --min-accepted-wrong-rows 10 \
  --min-physical-pairs 6 \
  --min-left-steps 5 \
  --min-checkpoints 2 \
  --min-targets 3 \
  --min-margin-buckets 2 \
  --min-success-drop-fraction 1.0 \
  --max-rows-per-pair-fraction 0.40 \
  --max-control-accepted-rows 0 \
  --run-dir runs/m116_boundary_wrong_history_robustness_seed9510
```

Artifacts:

```text
runs/m116_boundary_wrong_history_robustness_seed9510/summary.json
runs/m116_boundary_wrong_history_robustness_seed9510/robustness_gates.csv
runs/m116_boundary_wrong_history_robustness_seed9510/physical_pair_summary.csv
runs/m116_boundary_wrong_history_robustness_seed9510/accepted_wrong_history_rows.csv
```

## Result

Decision:

```text
reject_duplicate_dominated_boundary_surface
```

Aggregate metrics:

| Metric | Value |
| --- | ---: |
| M115 replay rows | 3045 |
| Wrong-history replay rows | 609 |
| Accepted wrong-history rows | 12 |
| Accepted physical source pairs | 3 |
| Accepted left steps | 3 |
| Accepted checkpoints | 2 |
| Accepted target groups | 3 |
| Accepted normal-margin buckets | 1 |
| Success-drop fraction | 1.0 |
| Max rows from one physical pair | 6 |
| Max rows / accepted rows | 0.5 |
| M62 accepted wrong-history rows | 0 |
| Accepted reset rows | 275 |
| Accepted zero-current rows | 332 |

Gate table:

| Gate | Observed | Required | Pass |
| --- | ---: | ---: | --- |
| accepted wrong rows | 12 | >= 10 | yes |
| physical source pairs | 3 | >= 6 | no |
| distinct left steps | 3 | >= 5 | no |
| checkpoints | 2 | >= 2 | yes |
| target groups | 3 | >= 3 | yes |
| normal-margin buckets | 1 | >= 2 | no |
| success-drop fraction | 1.0 | >= 1.0 | yes |
| max rows per physical pair fraction | 0.5 | <= 0.4 | no |
| M62 accepted rows | 0 | <= 0 | yes |

Physical source-pair summary:

| Physical pair | Rows | Checkpoints | Targets | Bucket |
| --- | ---: | --- | --- | --- |
| `9530:18:9540:21` | 2 | M102,M105 | lateral | 0.000-0.010 |
| `9530:21:9540:27` | 4 | M102,M105 | braking,lateral | 0.000-0.010 |
| `9530:24:9540:30` | 6 | M102,M105 | braking,lateral,yaw | 0.000-0.010 |

## Interpretation

M116 rejects direct objective training from M115.

The M115 signal is real but too concentrated:

- the `12` accepted rows are only `3` physical source pairs;
- all accepted rows are in one narrow boundary bucket around `0.006 m`;
- a single physical pair contributes `6 / 12` accepted rows;
- reset and zero-current degradation remain much more abundant.

This does not invalidate M115. It means M115 is a construction proof, not a
robust training corpus.

## Decision

Do not train a boundary-aware wrong-history objective yet.

Next task: M117 should mine or construct a more source-diverse wrong-history
boundary surface. The minimum target should be accepted wrong-history success
drops across more physical source pairs and more than one boundary bucket before
objective training is admitted.
