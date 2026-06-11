# M3223: B1 Moving-Obstacle Kinematics Smoke

Status: completed. This is an auxiliary env-engineering smoke only. It does
not train a policy, mutate the incumbent, admit validation ranking, or make a
driver-performance, high-fidelity sufficiency, paper, repair-success,
robustness-result, feasibility-proof, or self-ID claim.

## Artifacts

- Preregistration: `experiments/feasibility_audit/moving_obstacle_prereg.json`
- Quick smoke: `experiments/feasibility_audit/moving_obstacle_smoke_quick.json`
- Full smoke: `experiments/feasibility_audit/moving_obstacle_smoke.json`
- Frame rows: `runs/feasibility_audit/moving_obstacle_smoke/episode_rows.csv`
- Script: `scripts/feasibility_audit/moving_obstacle_smoke.py`

## Implementation

M3223 adds a non-default obstacle motion mode:

- default: `ObstacleTaskConfig.motion_mode="static"`
- new mode: `motion_mode="constant_velocity_crosser"`
- crosser velocity: `crosser_lateral_velocity_range`, sampled at reset and
  applied along the reset path normal at every env step

The obs72 shape is unchanged. Obstacle slots still use
`[present, x/80, y/20, rel_vx/20, rel_vy/12, half_width/5, half_width/5]`.

Legacy relative-velocity behavior is preserved:

- `obstacle_relative_velocity_mode="zero"` forces obstacle rel-v slots to
  exactly zero, even for moving obstacles.
- `obstacle_relative_velocity_mode="ego"` exposes ego-frame relative velocity;
  for moving obstacles this now includes the obstacle's world velocity.

Dynamic feasibility labels are re-derived in `classify_obstacle_scenario` by
recording `obstacle_lateral_velocity` and
`predicted_lateral_offset_at_arrival`, then computing the lateral offset still
required at the longitudinal arrival time. Static scenarios are the old formula
with zero lateral offset and zero lateral velocity.

## Smoke

The full smoke used 16 seeds over three modes:

- `legacy_static_zero_relvel`
- `moving_crosser_zero_relvel_contract`
- `moving_crosser_ego_relvel`

Budget: 48 episodes, 1,968 frames, 4 deterministic replay seeds.

| readout | result |
|---|---:|
| legacy/moving zero-relvel violations | 0 |
| moving body-y delta min | 0.6053 m |
| max ego rel-velocity norm | 19.9404 m/s |
| dynamic label rows with velocity fields | 1312 / 1312 |
| deterministic replay failures | 0 |

## Decision

Accept M3223 as completed B1. The moving-obstacle axis is now available behind
a non-default config flag, with deterministic replay and preserved legacy
zero-relvel behavior.

This does not make any controller outcome claim. Future moving-obstacle
measurements still need their own preregistered panels and criteria.

The next lowest OPEN roadmap item is B2 high-speed domain, which must apply
the M3221 normalization/preview recommendation before any population or
high-speed training.
