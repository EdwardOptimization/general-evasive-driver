# M322 Source-Diverse Protected Gate Implementation

M322 implements a reusable source-diverse protected gate wrapper. No PPO,
actor update, promotion, or actor-input change was performed.

## Implementation

New module:

```text
src/autodrift/source_diverse_protected_gate.py
```

New tests:

```text
tests/test_source_diverse_protected_gate.py
```

The wrapper:

- accepts repeated checkpoint policies;
- accepts repeated replay-gate specs in the form
  `name=corpus_csv,baseline_policy,candidate_policy`;
- runs each replay gate through the existing
  `boundary_outcome_replay_gate` implementation;
- ingests diagnostic CSVs such as the `9944` critical-key guard output;
- writes `summary.json`, `replay_gate_summary.csv`, and
  `diagnostic_summary.csv`;
- reports aggregate pass/fail and failure taxonomy.

The wrapper does not change actor inputs. It only reuses the existing
human-view replay gates.

## Focused Tests

Command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_source_diverse_protected_gate.py tests/test_boundary_outcome_replay_gate.py
```

Result:

```text
9 passed
```

## M320 Sanity Reproduction

Run dir:

```text
runs/m322_source_diverse_protected_gate_m320_sanity
```

The wrapper reproduces the M320 replay-sanity pass:

| Replay gate | Rows | Baseline drops | Candidate drops | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| m316_current | 17 | 17 | 17 | -0.000000521 | -0.000000197 | true |
| m314_continuity | 17 | 17 | 17 | +0.000000523 | +0.000000199 | true |
| m316_repaired_endpoint | 17 | 17 | 17 | -0.000194789 | -0.000080237 | true |

Aggregate:

| Metric | Value |
| --- | ---: |
| replay gate count | 3 |
| replay gates passed | 3 |
| replay gates failed | 0 |
| overall pass | true |

The wrapper also ingests the protected-key diagnostic:

| Diagnostic | Rows | Accepted rows | Accepted fraction | Normal margin max |
| --- | ---: | ---: | ---: | ---: |
| protected_key_9944 | 4 | 3 | 0.75 | 0.200336 |

## Interpretation

M322 is positive. It turns the manually repeated M320 replay checks into a
single reproducible source-diverse protected gate artifact. This reduces the
risk of manual command drift before future PPO proposals.

What it proves:

- the wrapper can aggregate M320 source-diverse protected replay gates;
- the wrapper keeps `9944` as a diagnostic CSV rather than silently deleting it;
- focused tests and real M320 sanity reproduction pass.

What it does not prove:

- that a future PPO candidate should be promoted if it fails `9944`;
- that the source-diverse gate accepts the repaired PPO endpoint;
- that PPO can continue safely.

The next step should be a diagnostic retrospective probe: run the new wrapper on
the M316 repaired endpoint as candidate and compare the source-diverse gate
result against the old `9944` diagnostic.

## Decision

Admit:

```text
m323-source-diverse-gate-retrospective-endpoint-probe
```

Decision:

```text
admit_m323_source_diverse_gate_retrospective_endpoint_probe
```
