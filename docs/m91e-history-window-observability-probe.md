# M91-E History-Window Observability Probe

M91-E adds explicit history-window support to the supervised input observability
audit. This tests whether past command-response frames improve future handling
envelope prediction over a current-frame probe.

This remains a supervised input audit. It does not train PPO and does not
promote a driver.

## Implementation

The audit now accepts:

```text
--history-windows 1,10,25,50,100
```

For each sampled state, the probe builds a concatenated history from past
observations only. Early samples are padded by repeating the earliest available
observation from the episode. No future observations are used.

Each history window is evaluated with the same feature profiles:

```text
p0_no_wheel_response_context
p1_wheel_response_context
p0_response_only
p1_response_only
wheel_only
context_only
```

The output `probe_summary.csv` and `profile_gain_summary.csv` now include
`history_window_steps`.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.input_observability_audit \
  --env-config configs/m91c_raw_wheel_minimum_profile.json \
  --episodes 40 \
  --seed 9340 \
  --policy heuristic \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 1000 \
  --ridge 0.1 \
  --history-windows 1,10,25,50,100 \
  --run-dir runs/m91e_history_window_observability_seed9340
```

Artifacts:

```text
runs/m91e_history_window_observability_seed9340/samples.csv
runs/m91e_history_window_observability_seed9340/probe_summary.csv
runs/m91e_history_window_observability_seed9340/profile_gain_summary.csv
runs/m91e_history_window_observability_seed9340/summary.json
runs/m91e_history_window_observability_seed9340/manifest.json
```

The run collected `790` sampled states, with an episode-disjoint train/test
split of `556` train samples and `234` test samples.

## Result

P1 minus P0 full-profile R2 by target and history window:

| target | 1 | 10 | 25 | 50 | 100 |
| --- | ---: | ---: | ---: | ---: | ---: |
| future braking decel | 0.046783 | 0.049235 | -0.007103 | -0.069392 | 0.286740 |
| future lateral accel response | -0.019239 | 0.037542 | 0.015313 | -0.193349 | 0.212450 |
| future yaw response | -0.011347 | -0.012059 | -0.029674 | 0.004727 | 0.832287 |

Absolute P1 full-profile R2 by target and history window:

| target | 1 | 10 | 25 | 50 | 100 |
| --- | ---: | ---: | ---: | ---: | ---: |
| future braking decel | 0.193755 | 0.019740 | -0.084536 | -1.004620 | -1.312575 |
| future lateral accel response | 0.379596 | 0.249988 | 0.292843 | -0.585095 | -1.348602 |
| future yaw response | -0.136348 | -0.159568 | -0.329269 | -1.879734 | -2.849927 |

Response-only P1 minus P0 R2:

| target | 1 | 10 | 25 | 50 | 100 |
| --- | ---: | ---: | ---: | ---: | ---: |
| future braking decel | 0.057451 | 0.031728 | 0.045825 | -0.288578 | -0.678011 |
| future lateral accel response | -0.010641 | 0.002375 | -0.010955 | -0.173092 | -0.636418 |
| future yaw response | -0.004722 | -0.067829 | -0.122514 | 0.090730 | 0.084555 |

## Interpretation

M91-E is a useful negative/mixed result for naive raw history concatenation.

Positive:

- The harness can now compare multiple history windows under the same seed,
  reward, policy, and target definitions.
- Short-window raw wheel P1 still improves braking response prediction.
- Some long-window P1-P0 R2 deltas are large, which means the wheel branch can
  change the regression result.

Negative:

- Absolute R2 generally gets worse as the raw concatenated history window grows.
- The large 100-step P1-P0 gains occur while both P0 and P1 have negative
  absolute R2, so they are not reliable self-ID evidence.
- Lateral and yaw targets do not show a stable monotonic benefit from raw wheel
  history.
- A linear ridge probe over 50-100 raw frames is too high-dimensional for the
  current sample size and likely overfits scene correlations.

## Decision

M91-E does not unblock M90 PPO continuation and does not justify profile RL
comparison yet.

The next step should keep the same supervised target structure but replace raw
history concatenation with compact command-response history features:

```text
M91-F: compact history observability probe.
```

Candidate compact features:

```text
current frame
current minus 0.2 s ago
current minus 0.5 s ago
window mean
window standard deviation
window min/max for response channels
```

This better matches the self-ID claim: the actor should not need a 100-frame
linear regressor; it needs a compact belief-relevant summary of how commands
changed vehicle response.
