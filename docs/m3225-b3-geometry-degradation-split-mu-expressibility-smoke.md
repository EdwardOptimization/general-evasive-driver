# M3225: B3 Geometry Degradation + Split-Mu Expressibility Smoke

Status: completed. This is an auxiliary env-contract implementation smoke and
expressibility audit only. It does not run training, mutate a driver, admit
Track C, or make a validation ranking, promotion, driver-performance,
current-sim robustness, high-fidelity sufficiency, paper, repair-success,
feasibility-proof, or self-ID claim.

## Artifacts

- Preregistration:
  `experiments/feasibility_audit/geometry_degradation_prereg.json`
- Quick smoke:
  `experiments/feasibility_audit/geometry_degradation_smoke_quick.json`
- Full smoke:
  `experiments/feasibility_audit/geometry_degradation_smoke.json`
- Frame rows:
  `runs/feasibility_audit/geometry_degradation_smoke/frame_rows.csv`
- Script:
  `scripts/feasibility_audit/geometry_degradation_smoke.py`

## Implementation

M3225 extends `ObservationDegradationConfig` with:

- `geometry_scope`: `none`, `road_boundary`, `obstacle_slots`, or
  `road_and_obstacle`
- `geometry_noise_std`: scalar Gaussian noise scale

The default remains `geometry_scope="none"` and `geometry_noise_std=0.0`, so
existing ego-response degradation configs keep their behavior. Geometry noise
uses a disjoint RNG substream from ego delay/noise/dropout.

For canonical obs72, geometry noise can target:

- road-boundary continuous channels, indices 12-43
- active obstacle-slot continuous channels, x/y/rel_vx/rel_vy

It deliberately leaves ego response, previous commands, obstacle present bits,
obstacle size fields, empty obstacle slots, privileged channels, rewards,
termination, and info untouched.

## Measurement

The full smoke ran 16 paired episodes and 400 paired frames. Each pair uses the
same seed and same scripted actions in a raw env and a geometry-degraded env.
The degraded profile was:

- `geometry_scope = "road_and_obstacle"`
- `geometry_noise_std = 0.04`

## Results

| readout | result |
|---|---:|
| obs72 shape pass | true |
| ego + command max delta | 0.000 |
| road boundary max delta | 0.159 |
| active obstacle continuous max delta | 0.132 |
| obstacle present + size max delta | 0.000 |
| empty obstacle slot max delta | 0.000 |
| termination consistency pass | true |
| deterministic replay failures | 0 |

## Split-Mu Expressibility

Left/right split-mu is not physically expressible in the current
`DriftObstacleEnv` outcome path. That path runs `SingleTrackDriftModel`, a
bicycle model with one scalar `VehicleParams.mu` and aggregated front/rear tire
forces. It has no left/right wheel contacts or per-side normal loads. Adding a
left/right split-mu flag there would be a fake label rather than a physical
obstacle-env mechanism.

The repository does contain source-only four-wheel HF0 primitives that can
express split-mu source shapes, but they are not integrated as the B3
obstacle-env outcome backend. Split-mu should be revisited for outcome panels
only after a backend exposes per-wheel or per-side contact patches and normal
loads through the executable env path.

## Decision

Accept M3225 as a completed B3 env-engineering milestone. Geometry-channel
degradation is now available behind an explicit config gate. Split-mu is
recorded as not expressible in the current `DriftObstacleEnv` single-track
path rather than implemented there as an unphysical proxy.

This does not admit training or controller performance claims. Future
geometry-degraded outcome panels still need preregistered labels, floors,
criteria, and seed streams.
