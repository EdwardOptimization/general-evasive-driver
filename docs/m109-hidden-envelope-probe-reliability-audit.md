# M109 Hidden-Envelope Probe Reliability Audit

M109 diagnoses why the hidden-envelope proof surface failed in M107/M108.

The audit asks whether the failure is caused by:

```text
target distribution shift across probe seeds;
train/test split variance;
insufficient sample count;
or genuinely weak recurrent hidden features.
```

## Implementation

Added:

```text
src/autodrift/hidden_envelope_reliability_audit.py
tests/test_hidden_envelope_reliability_audit.py
```

The audit records:

```text
target_distribution.csv
target_shift_summary.csv
split_probe_metrics.csv
split_lifts.csv
aggregate_lift_summary.csv
summary.json
```

It compares:

```text
checkpoints: M62, M102, M105
probe seeds: 9510, 9511, 9512
sample limits: 400, 800
split seeds: 9610, 9611, 9612, 9613, 9614
features: current_response, response_hidden, reset_response_hidden
targets: braking, lateral, yaw future envelope
```

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.hidden_envelope_reliability_audit \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --checkpoint-policy m62_a250=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --checkpoint-policy m102_9550=runs/m102_retention_actor_coupling_seed9550/optimized_checkpoint.pt \
  --checkpoint-policy m105_9710=runs/m105_anchor10_outcome_coupling_smoke_seed9710/optimized_checkpoint.pt \
  --probe-seeds 9510,9511,9512 \
  --split-seeds 9610,9611,9612,9613,9614 \
  --sample-limits 400,800 \
  --episodes 30 \
  --horizon-steps 15 \
  --sample-stride 3 \
  --ridge 0.1 \
  --device cpu \
  --mean-lift-threshold 0.0 \
  --min-lift-threshold 0.0 \
  --pass-fraction-threshold 1.0 \
  --run-dir runs/m109_hidden_envelope_reliability_audit_seed9510
```

## Target Stability

At `800` samples, target means are stable across probe seeds:

| checkpoint | target | mean of target mean | target mean range | mean target std |
| --- | --- | ---: | ---: | ---: |
| M62 | braking | 2.604464 | 0.027256 | 1.176145 |
| M62 | lateral | 1.186000 | 0.039760 | 1.107713 |
| M62 | yaw | 0.392085 | 0.006933 | 0.429882 |
| M102 | braking | 2.509734 | 0.022938 | 1.190247 |
| M102 | lateral | 1.230648 | 0.037464 | 1.123110 |
| M102 | yaw | 0.369607 | 0.007063 | 0.430097 |
| M105 | braking | 2.505245 | 0.021352 | 1.172883 |
| M105 | lateral | 1.221624 | 0.037438 | 1.114826 |
| M105 | yaw | 0.373458 | 0.007186 | 0.433708 |

This suggests the large hidden-lift swings are not primarily caused by probe
seed target means moving around. The target distribution is noisy, but the
between-seed target mean range is small after `800` samples.

## Split-Averaged Lift

`response_hidden_minus_reset_test_r2` across three probe seeds and five split
seeds:

| checkpoint | samples | target | lift mean | lift std | lift min | pass fraction |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| M62 | 400 | braking | -0.755427 | 1.016899 | -2.813443 | 0.1333 |
| M62 | 400 | lateral | -0.405713 | 0.658796 | -2.317427 | 0.2000 |
| M62 | 400 | yaw | 0.460274 | 1.638380 | -2.088879 | 0.7333 |
| M62 | 800 | braking | -0.134369 | 0.246106 | -0.503139 | 0.2000 |
| M62 | 800 | lateral | -0.185791 | 0.227713 | -0.778394 | 0.2000 |
| M62 | 800 | yaw | -0.448647 | 0.629208 | -1.558485 | 0.1333 |
| M102 | 400 | braking | -0.781051 | 0.988082 | -3.065215 | 0.2000 |
| M102 | 400 | lateral | -0.836753 | 1.877816 | -7.722539 | 0.0667 |
| M102 | 400 | yaw | -2.502430 | 4.218346 | -16.207824 | 0.2000 |
| M102 | 800 | braking | -0.173997 | 0.292696 | -1.010981 | 0.2000 |
| M102 | 800 | lateral | -0.323792 | 0.483278 | -1.269032 | 0.1333 |
| M102 | 800 | yaw | -0.358046 | 0.315621 | -0.841027 | 0.1333 |
| M105 | 400 | braking | -0.893595 | 1.016571 | -3.429213 | 0.2000 |
| M105 | 400 | lateral | -0.863082 | 1.903018 | -7.861152 | 0.0667 |
| M105 | 400 | yaw | -2.550061 | 4.442100 | -16.815762 | 0.2000 |
| M105 | 800 | braking | -0.138505 | 0.253025 | -0.786744 | 0.2000 |
| M105 | 800 | lateral | -0.459649 | 0.615920 | -1.665367 | 0.1333 |
| M105 | 800 | yaw | -0.457534 | 0.386813 | -1.138576 | 0.1333 |

Increasing from `400` to `800` samples reduces variance, but it does not make
response hidden beat reset hidden. The aggregate signal remains negative.

## Current-Response Baseline

At `800` samples, current response is often stronger than either hidden feature:

| checkpoint | target | current response mean R2 | response hidden mean R2 | reset hidden mean R2 |
| --- | --- | ---: | ---: | ---: |
| M62 | braking | 0.3334 | 0.1406 | 0.2749 |
| M62 | lateral | 0.0772 | -0.0422 | 0.1435 |
| M62 | yaw | 0.1653 | -0.3578 | 0.0909 |
| M102 | braking | 0.3944 | 0.1152 | 0.2892 |
| M102 | lateral | 0.1413 | -0.3245 | -0.0007 |
| M102 | yaw | 0.2497 | -0.1832 | 0.1748 |
| M105 | braking | 0.3853 | 0.1462 | 0.2847 |
| M105 | lateral | 0.1424 | -0.4367 | 0.0230 |
| M105 | yaw | 0.2489 | -0.3188 | 0.1388 |

This is the strongest diagnosis: the recurrent hidden state is not reliably
adding predictive information beyond the current response frame. Reset hidden
also often beats carried response hidden, which means the current hidden state
is not a stable belief representation for these envelope targets.

## Decision

M109 rejects the current hidden-envelope probe as an admission gate and rejects
another same-style hidden-retention objective.

The measurement is not useless: it shows the exact failure mode. Target means
are reasonably stable with `800` samples, and repeated splits still show that
current response dominates carried response hidden. The next direction should
train or gate a hidden representation against a current-response baseline, not
only against reset hidden.

M110 should test a current-response anchored hidden-envelope objective:

```text
train response hidden to predict future envelope targets;
gate response_hidden against current_response and reset_hidden;
use repeated split seeds and multi-seed aggregation;
do not proceed to PPO until hidden beats current response on braking/lateral/yaw.
```
