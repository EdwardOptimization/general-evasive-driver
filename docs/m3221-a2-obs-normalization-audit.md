# M3221: A2 Obs-Normalization Audit

Status: completed. This is an auxiliary observation-distribution audit only. It
does not apply a normalization change, mutate the incumbent, run training,
admit population training, or make a driver-performance, high-fidelity
sufficiency, paper, repair-success, robustness-result, feasibility-proof, or
self-ID claim.

## Artifacts

- Preregistration: `experiments/feasibility_audit/obs_normalization_prereg.json`
- Full summary: `experiments/feasibility_audit/obs_normalization_audit.json`
- Quick smoke: `experiments/feasibility_audit/obs_normalization_audit_quick.json`
- Channel table: `runs/feasibility_audit/obs_normalization_audit/channel_stats.csv`
- Episode table: `runs/feasibility_audit/obs_normalization_audit/episode_summary.csv`

## Measurement

M3221 executed roadmap A2: audit the canonical obs72 normalization constants
before any population or high-speed training.

The audit sampled three current-sim tiers:

- `S0_nominal`
- `C5_wide_current`: C5-wide mass/brake/drive/stiff/tau plus cg/Iz spread
- `S4_proxy_stress`: a current-sim stress proxy, not a validated passenger-fleet
  physics model

It ran three scripted profiles with the current obs72 contract:

- `mid_obstacle_arc`: R=60 m, 16 m/s, static obstacle
- `high_speed_arc`: R=250 m, 28 m/s, no obstacle
- `figure8_context`: R=45 figure-eight, 14 m/s, no obstacle

Budget: 144 episodes, 24,170 observations, 4.9 s CPU.

## Result

The audit flags a channel when `p99_abs > 0.9` or `frac_abs_gt_1 > 0.01`.
There are 107 saturated tier/profile/channel entries. The key failures are
not population mass alone; they are fixed-scale geometry and high-speed ego
channels.

| group | worst channel | tier/profile | max p99_abs | max frac | implication |
|---|---|---|---:|---:|---|
| road_y | road_right_7_y | C5_wide_current / mid_obstacle_arc | 2.045 | 0.591 | `y/20` is too small for curved far-boundary points |
| ego_accel | ego_ay | S0_nominal / high_speed_arc | 2.847 | 0.122 | `ax/15`, `ay/15` saturate in high-speed profiles |
| ego_speed | ego_vy | S0_nominal / high_speed_arc | 2.053 | 0.894 | `vx/20`, `vy/12` are not high-speed ready |
| obstacle_rel_speed | obs0_rel_vy | C5_wide_current / mid_obstacle_arc | 1.575 | 0.065 | `rel_vy/12` saturates with ego-relative obstacle mode |
| obstacle_y | obs0_y | S4_proxy_stress / mid_obstacle_arc | 1.008 | 0.010 | obstacle lateral scale is borderline |

Profile-specific worst readouts:

| profile | channel | tier | p99_abs | frac_abs_gt_1 | candidate divisor |
|---|---|---|---:|---:|---:|
| mid_obstacle_arc | road_right_7_y | C5_wide_current | 2.045 | 0.084 | 60 |
| mid_obstacle_arc | obs0_rel_vy | C5_wide_current | 1.575 | 0.065 | 25 |
| high_speed_arc | ego_vx | S0_nominal | 1.596 | 0.827 | 40 |
| high_speed_arc | ego_vy | S0_nominal | 2.053 | 0.217 | 40 |
| high_speed_arc | ego_ax | S0_nominal | 2.383 | 0.119 | 50 |
| high_speed_arc | ego_ay | S0_nominal | 2.847 | 0.093 | 60 |
| figure8_context | road_right_7_y | S0_nominal | 1.831 | 0.556 | 50 |

Preview-time readout:

| profile | speed | current road preview | preview time | preview for 2.5 s |
|---|---:|---:|---:|---:|
| mid_obstacle_arc | 16 m/s | 40 m | 2.500 s | 40 m |
| high_speed_arc | 28 m/s | 40 m | 1.429 s | 70 m |
| figure8_context | 14 m/s | 40 m | 2.857 s | 35 m |

At 36 m/s, the same 40 m road preview would be only 1.11 s.

## Recommendation

Population or high-speed training remains blocked on a follow-up
normalization/design implementation if it uses the audited stress envelopes.
M3221 only measures and recommends.

Candidate changes, not applied here:

- Change `ego_vx` divisor from 20 toward 40 and `ego_vy` divisor from 12
  toward 30-40 for >20 m/s work.
- Change `ax/ay` divisors from 15 toward 40-60 for high-speed maneuvers, or
  add robust clipping.
- Change `road_y` divisor from 20 toward 50-60, or redesign the road geometry
  encoding for curved tracks.
- Change obstacle relative-`vy` divisor from 12 toward 25 when
  `obstacle_relative_velocity_mode="ego"` is used.
- Make road lookahead distance speed-aware; 40 m is not enough preview for
  >20 m/s work.

## Decision

Accept M3221 as a completed A2 audit. A2 is DONE as a measurement, but it
creates a follow-up implementation blocker: do not start population or
high-speed training until the normalization/preview recommendation is turned
into an implementation milestone and re-smoked.

The next lowest OPEN roadmap unit is A3, C5' target consolidation, unless the
PI redirects to implement the A2 blocker first.
