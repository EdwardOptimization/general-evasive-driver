# M51: Margin-Retention Training And Gate

## Motivation

M50 showed that aggregate mean margin can hide the failure mode we care about.
M46 improves mean clearance margin over the combined M38/broad/fresh sweep, but
also creates more near-boundary regressions and preserves the known broad
success regression.

M51 turns that conclusion into a strict promotion gate and a continuation
training config.

## Gate

M51 adds:

- `src/autodrift/margin_retention_gate.py`;
- `tests/test_margin_retention_gate.py`;
- CLI script: `autodrift-margin-retention-gate`.

Input:

- full `seed_margin_deltas.csv` from `autodrift.margin_critical_corpus`.

Strict default checks:

- candidate success rate must not drop below baseline;
- binary regressed seeds must be zero;
- near-boundary margin-regressed seeds must be zero;
- mean clearance-margin delta must not be negative.

The gate writes:

- `candidate_gate_summary.csv`;
- `source_gate_summary.csv`;
- `gate_summary.json`;
- `gate_report.md`;
- `manifest.json`.

## Current-Candidate Gate Result

Command:

```bash
conda run -n autodrift python -m autodrift.margin_retention_gate \
  --seed-delta-csv runs/m50_margin_critical_corpus_m38_broad_fresh/seed_margin_deltas.csv \
  --min-success-delta 0.0 \
  --max-binary-regressed-seeds 0 \
  --max-near-margin-regressed-seeds 0 \
  --min-margin-delta-mean 0.0 \
  --run-dir runs/m51_margin_retention_gate_m50_strict
```

Result:

| Candidate | Passed | Success delta | Binary regressions | Near-margin regressions | Margin delta mean |
| --- | --- | ---: | ---: | ---: | ---: |
| m42_028 | false | 0.0000 | 0 | 3 | 0.002817 |
| m46_077 | false | 0.0000 | 1 | 4 | 0.004381 |
| m46_200 | false | 0.0000 | 1 | 10 | 0.005878 |

Artifacts:

- `runs/m51_margin_retention_gate_m50_strict/candidate_gate_summary.csv`;
- `runs/m51_margin_retention_gate_m50_strict/source_gate_summary.csv`;
- `runs/m51_margin_retention_gate_m50_strict/gate_report.md`.

Conclusion: no existing candidate is promotable under the strict
margin-retention gate. This is expected: M46 improves mean margin but fails
near-boundary retention.

## Training Config

M51 adds:

```text
configs/ppo_m51_margin_retention_driver.json
```

The config:

- starts from `m37_102`;
- uses the human-view online GRU actor;
- keeps deployable actor observations only;
- keeps the multi-step response-prediction auxiliary loss;
- removes the M46 paired-hidden action contrast objective;
- oversamples the M50 top-100 margin-critical corpus with
  `training_seed_mix_probability = 0.70`.

It does not add clearance margin, collision labels, hidden vehicle parameters,
controller mode, or oracle fields to the actor input.

Smoke command:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m51_margin_retention_driver.json \
  --total-steps 4096 \
  --rollout-steps 128 \
  --seed 2151 \
  --device cuda \
  --init-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt \
  --run-dir runs/ppo_m51_margin_retention_smoke_seed2151
```

Smoke result:

- init load mode: `strict`;
- final eval return mean: `67.180`;
- final eval termination rate: `0.100`;
- checkpoint: `runs/ppo_m51_margin_retention_smoke_seed2151/checkpoint.pt`.

## Smoke Gate

The 4096-step smoke checkpoint is not expected to pass, but it verifies that
the training output can feed the M51 gate.

Combined M38/broad/fresh smoke result versus `m37_102`:

| Candidate | Passed | Success delta | Binary regressions | Near-margin regressions | Margin delta mean |
| --- | --- | ---: | ---: | ---: | ---: |
| m51_smoke | false | -0.0125 | 2 | 6 | -0.011257 |

Artifacts:

- `runs/m51_smoke_margin_critical_corpus/seed_margin_deltas.csv`;
- `runs/m51_smoke_margin_retention_gate_strict/candidate_gate_summary.csv`;
- `runs/m51_smoke_margin_retention_gate_strict/source_gate_summary.csv`.

Conclusion: the smoke only proves wiring. It is a negative checkpoint result
and must not be promoted.

## Next Step

M52 should run the full M51 continuation training from `m37_102`, then evaluate
checkpoint sweeps through:

- M51 strict margin-retention gate;
- M50 margin-critical corpus;
- broad same-seed success;
- hidden-swap/action-trajectory gates.

Promotion requires passing M51 without weakening the existing self-identification
and aggregate-success gates.
