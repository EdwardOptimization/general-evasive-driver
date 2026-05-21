# M107 Multi-Seed Hidden-Envelope Gate

M107 addresses the M106 blocker: a single hidden-envelope probe seed can make
M105 look positive, while fresh probe seeds show negative lateral/yaw or
braking lift. The goal is to make hidden-envelope admission an aggregate gate
rather than a one-seed diagnostic.

## Implementation

Added:

```text
src/autodrift/hidden_envelope_multiseed_gate.py
tests/test_hidden_envelope_multiseed_gate.py
```

The wrapper reuses `run_hidden_envelope_probe(...)` and evaluates:

```text
checkpoints x probe seeds x targets
```

It writes:

```text
probe_lifts.csv
hidden_gain_rows.csv
aggregate_summary.csv
gate_summary.csv
summary.json
```

Per checkpoint and target, it reports:

```text
lift_mean
lift_min
lift_max
pass_count
pass_fraction
```

The current gate requires:

```text
mean lift >= 0
minimum lift >= 0
pass fraction >= 1.0
```

This is intentionally strict because the hidden state should not be admitted as
a reliable self-identification belief if a fresh probe seed flips the result.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.hidden_envelope_multiseed_gate \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --checkpoint-policy m105_9710=runs/m105_anchor10_outcome_coupling_smoke_seed9710/optimized_checkpoint.pt \
  --checkpoint-policy m105_9711=runs/m105_anchor10_outcome_coupling_smoke_seed9711/optimized_checkpoint.pt \
  --checkpoint-policy m105_9712=runs/m105_anchor10_outcome_coupling_smoke_seed9712/optimized_checkpoint.pt \
  --probe-seeds 9510,9511,9512 \
  --episodes 30 \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 800 \
  --ridge 0.1 \
  --device cpu \
  --mean-lift-threshold 0.0 \
  --min-lift-threshold 0.0 \
  --pass-fraction-threshold 1.0 \
  --run-dir runs/m107_multiseed_hidden_envelope_gate_seed9510
```

## Results

| checkpoint | target | mean lift | min lift | max lift | pass fraction |
| --- | --- | ---: | ---: | ---: | ---: |
| M105 9710 | braking | 4.081331 | -0.266590 | 12.299186 | 0.6667 |
| M105 9710 | lateral | -0.787382 | -2.270934 | 0.557126 | 0.3333 |
| M105 9710 | yaw | -0.865335 | -1.595636 | 0.033114 | 0.3333 |
| M105 9711 | braking | 4.173921 | -0.260660 | 12.550788 | 0.6667 |
| M105 9711 | lateral | -0.802924 | -2.378211 | 0.616504 | 0.3333 |
| M105 9711 | yaw | -0.854602 | -1.561755 | 0.037736 | 0.3333 |
| M105 9712 | braking | 4.236328 | -0.261113 | 12.734495 | 0.6667 |
| M105 9712 | lateral | -0.837288 | -2.468369 | 0.602892 | 0.3333 |
| M105 9712 | yaw | -0.882889 | -1.643308 | 0.013037 | 0.3333 |

The multi-seed gate fails for every checkpoint-target pair. Braking has a
positive mean only because seed `9511` gives a very large positive lift while
seed `9512` is negative. Lateral and yaw have negative mean lift for all three
checkpoints.

## Decision

M107 rejects M105 hidden-envelope admission under the multi-seed gate.

The behavior evidence from M106 remains useful, but the hidden belief evidence
is not robust. The next step should compare M98/M102/M105 under the same
multi-seed gate before changing objectives. If M98/M102 also fail, the probe
surface or target split is too unstable; if M102 passes and M105 fails, the
M105 action-anchor/outcome update damaged hidden belief despite behavior
retention.
