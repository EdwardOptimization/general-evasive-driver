# M356 Exact Repair Best-Step Selection Implementation

M356 fixes the exact post-PPO repair endpoint-selection issue found by M355.
It does not run PPO and does not promote a checkpoint.

## Problem

Before M356, `exact_post_ppo_repair` saved the final optimizer state
unconditionally. M355 showed this can discard a feasible intermediate state:

```text
M354 step 39: exact M297/M270 pass
M354 step 40 final checkpoint: exact M270 regresses
```

The repair trace also logged pre-update metrics, which made the final
checkpoint look safer than it actually was.

## Implementation

`src/autodrift/exact_post_ppo_repair.py` now:

- records post-update exact metrics for logged repair steps;
- writes a full `selection_trace.csv` with every post-update repair state;
- records a `final_optimizer_state` policy row separately from the saved
  candidate;
- supports `--selection-policy {best_feasible,final}`;
- defaults to `best_feasible`;
- saves the best lexicographically feasible checkpoint instead of blindly
  saving the final optimizer state.

Selection order:

```text
1. exact M297 and exact M270 no-regression pass;
2. lower positive exact violation if no feasible step exists;
3. lower total repair loss;
4. lower parameter distance to base;
5. earlier step as final tie-break.
```

This keeps the exact objectives as hard gates while using the repair loss to
choose among feasible states.

## M354 Repair Probe With New Selection

Run dir:

```text
runs/m356_m354_repair_best_step_probe
```

The corrected repair tool reuses the same M354 raw PPO checkpoint and repair
settings, but with default `best_feasible` selection.

| Policy row | Step | Exact M297 delta | Exact M270 delta | Pass |
| --- | ---: | ---: | ---: | --- |
| final optimizer state | 40 | -0.000023007 | +0.000040591 | false |
| saved candidate | 25 | -0.000157595 | -0.000097871 | true |

Candidate:

```text
runs/m356_m354_repair_best_step_probe/candidate_checkpoint.pt
```

The saved candidate now matches the exact gate result reported in
`candidate_summary.csv`: M297 and M270 both pass no-regression versus M352.

## Tests

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_exact_post_ppo_repair.py
```

Result:

```text
5 passed
```

Compile check:

```bash
python -m compileall -q src tests
```

Result:

```text
pass
```

## Interpretation

M356 does not prove the M354 repaired candidate is promotable. It only fixes the
infrastructure bug that prevented exact repair from preserving a feasible
intermediate state.

The next step is to treat the M356 candidate as the repaired M354 candidate and
run the proof-gate stack that M354 skipped after exact failure.

## Decision

Admit:

```text
m357-m354-best-step-repair-proof-gate
```

Decision:

```text
admit_m357_m354_best_step_repair_proof_gate
```
