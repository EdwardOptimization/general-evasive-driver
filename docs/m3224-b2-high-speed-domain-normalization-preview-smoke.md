# M3224: B2 High-Speed Domain Normalization/Preview Smoke

Status: completed. This is an auxiliary env-contract implementation smoke
only. It does not run training, mutate a driver, admit Track C, or make a
validation ranking, promotion, driver-performance, current-sim robustness,
high-fidelity sufficiency, paper, repair-success, feasibility-proof, or self-ID
claim.

## Artifacts

- Preregistration:
  `experiments/feasibility_audit/high_speed_domain_prereg.json`
- Quick smoke:
  `experiments/feasibility_audit/high_speed_domain_smoke_quick.json`
- Full smoke:
  `experiments/feasibility_audit/high_speed_domain_smoke.json`
- Frame rows:
  `runs/feasibility_audit/high_speed_domain_smoke/episode_rows.csv`
- Script:
  `scripts/feasibility_audit/high_speed_domain_smoke.py`

## Implementation

M3224 adds `ObservationScaleConfig` to `DriftEnvConfig`. The defaults reproduce
the legacy obs72 contract:

- ego velocity and acceleration: `vx/20`, `vy/12`, `ax/15`, `ay/15`
- road points: `(x/80, y/20)`
- obstacle slots: `[present, x/80, y/20, vx/20, vy/12, half_width/5, half_length/5]`
- fixed road preview: 8 points at 5 m spacing, max 40 m

The B2 high-speed profile is explicit and non-default:

- `max_speed_limit = 45.0`
- `ego_vx = 40`, `ego_vy = 40`
- `ego_ax = 50`, `ego_ay = 60`
- `road_y = 60`
- `obstacle_rel_vy = 30`
- `road_lookahead_time_s = 2.5`
- `road_lookahead_max_distance = 120`

The road preview keeps the same number of observation points and therefore the
same obs shape. When `road_lookahead_time_s > 0`, the final road point is placed
at `max(legacy_40m, speed * target_time)`, capped by
`road_lookahead_max_distance` without shortening the legacy 40 m baseline.

## Measurement

The full smoke ran 48 episodes and 1776 frames across three modes:

- `legacy_fixed_preview`
- `scaled_high_speed`
- `scaled_high_speed_crosser`

The fixture uses 36 m/s on a 250 m circular track. The crosser profile adds a
constant-velocity obstacle with a 24 m/s lateral crossing speed so high-speed
feasibility labels and obstacle relative-velocity scaling are exercised.

## Results

| readout | result |
|---|---:|
| obs72 shape pass | true |
| high-speed reached pass | true |
| legacy saturation exposed | true |
| legacy `ego_vx` max abs | 1.800 |
| legacy preview time min | 1.111 s |
| scaled normalization pass | true |
| scaled selected-channel max abs | 0.900 |
| scaled preview time min | 2.500 s |
| high-speed label rows | 592/592 |
| deterministic replay failures | 0 |

Selected full-smoke maxima:

| mode | ego_vx | ego_vy | ego_ax | ego_ay | road_y | obs_rel_vy |
|---|---:|---:|---:|---:|---:|---:|
| legacy_fixed_preview | 1.800 | 0.243 | 0.045 | 0.920 | 0.894 | 0.000 |
| scaled_high_speed | 0.900 | 0.073 | 0.013 | 0.230 | 0.618 | 0.000 |
| scaled_high_speed_crosser | 0.900 | 0.073 | 0.013 | 0.230 | 0.618 | 0.870 |

## Decision

Accept M3224 as a completed B2 env-engineering milestone. The M3221
high-speed obs-normalization/preview blocker is closed for the explicit B2
profile: 36 m/s scenarios can now be represented with bounded selected channels
and a 2.5 s road preview while preserving the legacy default obs72 contract.

This does not admit population training, Track C training, controller
performance claims, or high-speed robustness claims. Future high-speed outcome
panels still need their own preregistered labels, floors, criteria, and seed
streams.
