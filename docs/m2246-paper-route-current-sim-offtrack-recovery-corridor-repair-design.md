# M2246 Paper-Route Current-Sim Offtrack/Recovery/Corridor Repair Design

- status: completed
- decision: `current_sim_offtrack_recovery_corridor_repair_design_admit_reward_extension_materialization`
- manifest: `experiments/manifests/m2246-paper-route-current-sim-offtrack-recovery-corridor-repair-design.json`
- parent audit: `docs/m2245-paper-route-current-sim-selected-checkpoint-outcome-localization-result-audit.md`

## Design Premise

M2244/M2245 show that the selected-checkpoint panel is blocked primarily by
road containment, not by missing execution infrastructure:

```text
episodes: 480
success: 277 / 480
offtrack: 110 / 480
collision: 93 / 480
max-step noncompletion: 0 / 480
dominant failure mode: offtrack_dominated_failure
```

The current training configs already use:

```text
track_width: 8.5
termination_penalty: 8.0
collision_penalty: 25.0
stable_aes_sideslip_penalty: 2.8
dense_clearance_margin_reward_scale: 0.0
clearance_margin_reward_scale: 0.0
```

The environment reward currently has hard-coded road tracking terms:

```text
- 2.4 * track_cost
- 0.25 * heading_cost
```

and offtrack termination is generic:

```text
if abs(frame.lateral_error) > track_width:
    return "off_track"
```

So the next repair should not be another budget escalation or checkpoint search.
It should make road-containment pressure explicit and configurable while keeping
collision/clearance as a guardrail.

## Rejected Shortcuts

Do not use these as primary repair variables:

```text
widen track_width
move obstacle farther away only to improve success
drop drift-required/unavoidable labels
change actor input contract
profile-specific tuning
rank profiles from this diagnostic panel
```

Those would make the task easier or change the comparison boundary without
showing that the driver learned better containment.

## Repair Design

M2247 should implement a no-training reward/config extension and materialize a
repaired matched-budget config matrix.

Add configurable road-containment reward terms to `DriftEnvConfig`:

```text
track_cost_scale: default 2.4
heading_cost_scale: default 0.25
road_margin_cost_scale: default 0.0
road_margin_warning_fraction: default 0.70
off_track_penalty: default 0.0
```

The default values must preserve old behavior exactly:

```text
road_margin_cost_scale == 0.0
off_track_penalty == 0.0
track_cost_scale == old hard-coded 2.4
heading_cost_scale == old hard-coded 0.25
```

The repaired config family should use one shared setting for all profiles and
seeds:

```text
track_cost_scale: 2.8
heading_cost_scale: 0.25
road_margin_cost_scale: 1.2
road_margin_warning_fraction: 0.65
off_track_penalty: 6.0
dense_clearance_margin_reward_scale: 0.5
dense_clearance_margin_reward_window: 10.0
clearance_margin_reward_scale: 1.0
clearance_margin_reward_clip: 0.25
termination_penalty: 8.0
collision_penalty: 25.0
track_width: 8.5
```

The road-margin cost should activate before termination:

```text
margin_fraction = abs(lateral_error) / track_width
excess = max(margin_fraction - road_margin_warning_fraction, 0)
normalized_excess = excess / max(1 - road_margin_warning_fraction, eps)
road_margin_cost = normalized_excess ** 2
reward -= road_margin_cost_scale * road_margin_cost
```

`off_track_penalty` should be charged only when termination reason is
`off_track`. It must be separate from generic `termination_penalty` so future
audits can distinguish road departure from collision and other terminations.

## Curriculum Boundary

The first repaired config wave should stay matched to the current panel:

```text
profiles: L0_current_masked, L1_one_step, L2_window_25, L2_window_50, L3_online_gru
seeds: 222601, 222602, 222603
total_steps: 32768
checkpoint_interval_steps: 4096
eval_episodes: 32
num_envs: 4
rollout_steps: 128
update_epochs: 2
learning_rate: 0.0001
```

Do not introduce a new obstacle distribution in the same first repair. If the
reward repair still leaves offtrack dominant, then route to a separate
task-curriculum stratification design.

## Guardrails

Future execution can only become comparison-ready if it improves containment
without hiding collision risk:

```text
selected_checkpoint_profile_floor_pass_count >= 1
selected beats final should remain tracked
global offtrack rate < 0.20 on selected-checkpoint localization
global collision rate <= M2244 collision rate + 0.03
max-step noncompletion remains 0 or near 0
guardrail_violation_count == 0
ranking_admissible_count == 0 until readiness floors pass
```

The collision guardrail is intentionally explicit. A repair that reduces
offtrack by driving into obstacles is a failure, not progress.

## Follow-Up

The design admits reward-extension materialization, but the workflow cadence
requires a synthesis milestone before implementation. Next:

```text
m2247-paper-route-current-sim-task-curriculum-readiness-branch-synthesis
```

If that synthesis decides `continue`, the following implementation should add
the reward/config extension and produce a no-training config matrix. It should
not run training, rollout, measured execution, replay, PPO, private holdout,
profile ranking, paper-level comparison, finite-window vs GRU verdict, or
level3 self-identification evaluation.
