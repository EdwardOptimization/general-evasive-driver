# M242 Exact Outcome Objective Evaluator

M242 adds deterministic full-corpus outcome objective evaluation to the existing
`outcome_intervention_eval` harness. No PPO is run in this milestone.

Actor inputs are unchanged.

## Implementation

`src/autodrift/outcome_intervention_eval.py` now supports:

```text
--exact
```

Default behavior is unchanged: without `--exact`, the evaluator uses sampled
fixed batches and reports `mode=sampled`.

With `--exact`, the evaluator computes the outcome intervention loss once over
all snippet rows:

```text
preferred_log_prob = log pi(preferred_action | observation, preferred_hidden)
rejected_log_prob  = log pi(preferred_action | observation, rejected_hidden)
loss = weighted_mean(softplus(rejected_log_prob - preferred_log_prob + margin), weight)
```

Exact-mode outputs are explicit:

```text
mode=exact
batch_size=<number of snippet rows>
batches=1
loss_std=0
```

This avoids mixing sampled and deterministic metrics in future promotion gates.

## Tests

Focused tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_outcome_intervention_eval.py tests/test_intervention_objectives.py
```

Result:

```text
15 passed in 0.88s
```

Syntax check:

```text
python -m compileall -q src tests
```

Result: pass.

## Exact Smoke

M232 exact evaluation:

```text
runs/m242_exact_m232_outcome_eval
```

| Policy | Loss |
| --- | ---: |
| m224 | 0.244663 |
| m237_raw | 0.244636 |
| m239_a500 | 0.244649 |
| m240_raw | 0.244676 |
| m240_a500 | 0.244669 |

M223 exact evaluation:

```text
runs/m242_exact_m223_outcome_eval
```

| Policy | Loss |
| --- | ---: |
| m224 | 0.209025 |
| m237_raw | 0.208989 |
| m239_a500 | 0.209007 |
| m240_raw | 0.209022 |
| m240_a500 | 0.209023 |

These reproduce the M241 audit:

- M237 improves M232 and M223.
- M239 keeps part of the improvement.
- M240 regresses M232 while only slightly improving M223.

## Decision

M242 completes as infrastructure.

Next step:

```text
m243-exact-gated-ppo-smoke-from-m239
```

M243 should start from the current public-gate base `m239_a500`, run exactly one
PPO smoke, then use interpolation plus exact M232/M223 objectives, proof gates,
and behavior gates before any candidate can be accepted.
