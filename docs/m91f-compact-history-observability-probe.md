# M91-F Compact History Observability Probe

M91-F tests compact command-response history summaries after M91-E showed that
naive raw history concatenation degrades at long windows.

This remains a supervised input audit. It does not train PPO and does not
promote a driver.

## Implementation

The audit now accepts:

```text
--history-mode summary
```

For each history window, summary mode emits six 85-value blocks:

```text
current frame
current - first frame in window
window mean
window standard deviation
window min
window max
```

The same P0/P1 profile slicing is then applied to the summary blocks, so raw
wheel channels are compared against no-wheel channels at identical windows.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.input_observability_audit \
  --env-config configs/m91c_raw_wheel_minimum_profile.json \
  --episodes 40 \
  --seed 9350 \
  --policy heuristic \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 1000 \
  --ridge 0.1 \
  --history-windows 10,25,50 \
  --history-mode summary \
  --run-dir runs/m91f_compact_history_observability_seed9350
```

Artifacts:

```text
runs/m91f_compact_history_observability_seed9350/samples.csv
runs/m91f_compact_history_observability_seed9350/probe_summary.csv
runs/m91f_compact_history_observability_seed9350/profile_gain_summary.csv
runs/m91f_compact_history_observability_seed9350/summary.json
runs/m91f_compact_history_observability_seed9350/manifest.json
```

The run collected `771` sampled states, with an episode-disjoint train/test
split of `540` train samples and `231` test samples.

## Result

P1 minus P0 full-profile R2:

| target | 10 | 25 | 50 |
| --- | ---: | ---: | ---: |
| future braking decel | 0.110127 | 0.085119 | -0.221516 |
| future lateral accel response | -0.003372 | -0.049506 | -0.128158 |
| future yaw response | 0.065229 | -0.047603 | -0.273799 |

Absolute P1 full-profile R2:

| target | 10 | 25 | 50 |
| --- | ---: | ---: | ---: |
| future braking decel | -0.489779 | -0.548381 | -0.824440 |
| future lateral accel response | 0.393141 | 0.295670 | 0.076199 |
| future yaw response | -0.512764 | -0.934580 | -1.248071 |

Response-only P1 minus P0 R2:

| target | 10 | 25 | 50 |
| --- | ---: | ---: | ---: |
| future braking decel | 0.039637 | -0.003920 | -0.176414 |
| future lateral accel response | 0.037102 | -0.016055 | -0.172261 |
| future yaw response | -0.127133 | -0.140916 | -0.168354 |

## Interpretation

M91-F is a negative result for the current hand-built compact summary.

Positive:

- Summary mode runs and preserves P0/P1 comparability.
- At the 10-step window, raw wheel P1 improves full-profile braking and yaw R2
  over P0.
- Lateral acceleration remains learnable from the summary profile.

Negative:

- Braking and yaw absolute R2 are still negative.
- The wheel advantage does not persist at 25 and 50 steps.
- Response-only P1 gains are not stable.
- Compared with M91-E, summary mode helps control dimensionality but does not
  produce a robust self-ID signal.

## Decision

M91-F does not unblock M90 PPO continuation and does not justify minimum-set
sensor ablations yet.

The next step should test a learned supervised history encoder before returning
to PPO:

```text
M91-G: learned history encoder observability probe.
```

Rationale: professional-driver self-identification is a belief-learning problem.
A linear probe over raw or hand-summary history may be too weak to detect useful
closed-loop response information even if such information exists.
