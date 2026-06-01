# M2258 Paper-Route Current-Sim Midcourse Corridor-Containment Repair Design

- status: completed
- decision: `current_sim_midcourse_corridor_containment_repair_design_admit_config_materialization`
- manifest: `experiments/manifests/m2258-paper-route-current-sim-midcourse-corridor-containment-repair-design.json`
- parent audit: `docs/m2257-paper-route-current-sim-offtrack-failure-slice-diagnosis-result-audit.md`

## Design Premise

M2256/M2257 localized the failed reward repair:

```text
global success/offtrack/collision delta: -8/+8/0
mid_offtrack_delta: +14
late_offtrack_delta: -6
mild_overshoot_delta: +11
severe_overshoot_delta: 0
safe_clearance_offtrack_delta: +7
```

This is a midcourse mild boundary-containment problem, not a collision-only
problem and not a severe-loss-of-control problem. The previous repair increased
return but failed the intended outcome.

## Repair Principle

The next repair must target dense road-boundary containment before termination,
not just increase terminal offtrack penalty or optimize return.

Keep fixed:

```text
track_width: 8.5
actor observation contract
profile set
seed set
collision_penalty: 25.0
dense_clearance_margin_reward_scale: 0.5
dense_clearance_margin_reward_window: 10.0
clearance_margin_reward_scale: 1.0
clearance_margin_reward_clip: 0.25
```

Change only shared reward shaping terms for all profiles and seeds:

```text
track_cost_scale: 3.0
heading_cost_scale: 0.30
road_margin_cost_scale: 2.6
road_margin_warning_fraction: 0.50
off_track_penalty: 8.0
```

Rationale:

- `road_margin_warning_fraction=0.50` starts dense containment pressure earlier.
- `road_margin_cost_scale=2.6` makes mild overshoot less attractive before
  termination.
- `track_cost_scale=3.0` increases center/corridor pressure without widening the
  road.
- `heading_cost_scale=0.30` modestly favors alignment while avoiding a major
  behavior rewrite.
- `off_track_penalty=8.0` is only a secondary terminal pressure; the primary
  repair is dense midcourse containment.

## Matched Panel

Materialize the same matched profile/seed budget:

```text
profiles:
  L0_current_masked
  L1_one_step
  L2_window_25
  L2_window_50
  L3_online_gru

seeds:
  222601
  222602
  222603

total_steps: 32768
checkpoint_interval_steps: 4096
eval_episodes: 32
num_envs: 4
rollout_steps: 128
update_epochs: 2
learning_rate: 0.0001
```

Do not add a new scenario distribution in the same repair. The question is
whether targeted containment shaping changes the known M2256 failure slices.

## Acceptance Criteria For Later Execution

The later training/outcome-localization path must be judged by slice metrics:

```text
mid_offtrack_delta vs M2244 <= 0
mild_overshoot_delta vs M2244 <= 0
global_offtrack_count < 110
global_collision_count <= 93 + 14
max_step_noncompletion_count == 0
selected_checkpoint_profile_floor_pass_count >= 1 or clear local support increase
```

Return improvement alone is explicitly insufficient.

If the next repaired panel improves return but leaves:

```text
mid_offtrack_delta > 0
or mild_overshoot_delta > 0
or collision_count > 107
```

then the repair fails and should route to synthesis or task redesign, not
another scalar reward tweak.

## Guardrails

M2258 and M2259 must not:

```text
run environment reset
run environment rollout
execute policy actions
run measured execution
train
run replay
run PPO
use private holdout
promote any checkpoint
rank profiles
select a winner
change actor observation contract
claim finite-window-vs-GRU
claim level3 self-identification
claim paper-level result
```

## Next

Pre-register:

```text
m2259-paper-route-current-sim-midcourse-corridor-containment-config-materialization
```
