# M323 Source-Diverse Gate Retrospective Endpoint Probe

M323 uses the new source-diverse protected gate wrapper to diagnose the M316
repaired endpoint. No PPO, actor update, promotion, or actor-input change was
performed.

## Wrapper Hardening

The first M323 attempt exposed an invalid gate-spec case: a replay gate cannot
use the same policy as both baseline and candidate. The wrapper now rejects that
case directly with a focused test, rather than letting the lower-level replay
merge fail with duplicate `row_id` keys.

Focused command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_source_diverse_protected_gate.py
```

Result:

```text
5 passed
```

## Endpoint Probe

Run dir:

```text
runs/m323_source_diverse_gate_repaired_endpoint_probe
```

Candidate:

```text
runs/m316_exact_repair_from_raw_s40_seed10096/candidate_checkpoint.pt
```

The source-diverse replay bundle passes:

| Replay gate | Rows | Baseline | Candidate | Baseline drops | Candidate drops | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | --- |
| current_vs_repaired | 17 | m316_a0_0025 | m316_repaired | 17 | 17 | +0.000194793 | +0.000080242 | true |
| previous_vs_repaired | 17 | m314_base | m316_repaired | 17 | 17 | +0.000195316 | +0.000080442 | true |

Aggregate:

| Metric | Value |
| --- | ---: |
| replay gate count | 2 |
| replay gates passed | 2 |
| replay gates failed | 0 |
| overall pass | true |

## Old-Key Diagnostic

Diagnostic CSV:

```text
runs/m316_protected_key_sweep/guard_results.csv
```

| Diagnostic | Rows | Accepted rows | Accepted fraction | Normal margin min | Normal margin max | Margin gap min |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| protected_key_sweep | 13 | 3 | 0.230769 | 0.199909 | 0.207388 | 0.096982 |

The repaired endpoint corresponds to the alpha `1.0` direction in the sweep and
fails the old single-key normal-margin window, while the source-diverse M320
bundle passes.

## Interpretation

M323 is a diagnostic positive. It confirms the conflict M318/M321 were designed
to expose:

```text
M316 repaired endpoint:
  passes source-diverse protected replay bundle
  fails old saturated 9944 single-key window
```

This does not promote the endpoint. It means the project now needs an explicit
policy for how to handle candidates that pass source-diverse protected surfaces
but fail `9944` only by the old singleton normal-margin window.

## Decision

Admit:

```text
m324-single-key-window-override-policy-design
```

Decision:

```text
admit_m324_single_key_window_override_policy_design
```
