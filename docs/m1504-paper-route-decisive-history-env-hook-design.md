# M1504 Paper-Route Decisive History Env-Hook Design

## Summary

M1504 designs the no-training current-sim hook layer needed to turn M1503
metadata source plans into real simulator candidate-generation probes.

Decision:

```text
decisive_history_env_hook_design_admit_env_hook_implementation
```

This milestone is design only. It does not run simulator rollout probes,
replay, PPO, training, promotion, private holdout, corpus export, actor-input
changes, or level3 self-ID claims.

## Design Question

M1503 proved only that source-plan metadata can satisfy public scale/diversity
thresholds. M1504 asks:

```text
What minimal current-sim hook layer is needed to test whether the six T4/T5
source families can produce real DecisiveHistoryTaskCandidate rows?
```

The answer should be implemented before any rollout probe so simulator evidence
does not get mixed with design decisions.

## Current Simulator Support

The existing `AutoDriftEnv` already exposes useful building blocks:

```text
DriftEnvConfig
FrictionStepConfig
ObstacleTaskConfig
WarmupGateConfig
RandomizationConfig
AutoDriftEnv.reset(seed=..., options=...)
AutoDriftEnv.step(action)
AutoDriftEnv._info(...)
```

Relevant no-actor diagnostic fields already exist in `info`:

```text
mu, initial_mu
mass_scale, inertia_scale, cg_shift
front_tire_stiffness_scale, rear_tire_stiffness_scale, tire_stiffness_scale
drive_scale, brake_scale, steer_tau_scale, drive_tau_scale
step, friction_step_at, friction_step_applied
obstacle_perception_visible, obstacle_label
obstacle_distance, obstacle_lateral_offset
min_clearance_margin, collision, obstacle_completed
active_obstacle_kind, active_obstacle_body_x, active_obstacle_body_y
warmup_gate_visible, warmup_gate_passed, warmup_gate_collision
warmup_gate_distance, warmup_gate_clearance_margin
```

These fields may be used by hooks, miners, labels, and diagnostics. They must
not enter deployable actor observations.

## Hook Boundary

M1505 should add a module with only hook/spec plumbing, for example:

```text
src/autodrift/decisive_history_env_hooks.py
```

Suggested public dataclasses:

```text
DecisiveHistoryEnvHookSpec
  source_family
  task_family
  seed
  capability_pair
  geometry_key
  reveal_step
  decision_step
  env_config
  warmup_mode
  capability_variant
  obstacle_variant
  labels_enter_actor_input

DecisiveHistoryTracePoint
  seed
  source_family
  step
  observation
  action
  info_subset

DecisiveHistoryHookArtifacts
  specs
  trace_schema
  candidate_schema
  guardrails
```

Suggested functions:

```text
source_plan_to_hook_specs(plan, *, max_specs=None)
default_hook_specs(seed_count)
env_config_for_hook_spec(spec)
hook_spec_to_candidate_stub(spec)
hook_spec_to_row(spec)
build_env_hook_summary(specs)
run_env_hook_dry_smoke(run_dir, seed_count)
```

M1505 should not need a checkpoint, policy, replay gate, trainer, private
holdout, or rollout continuation. A dry smoke may instantiate specs and env
configs, but full simulator rollout should wait for a later runtime smoke.

## Source-Family Mapping

The six M1501/M1503 source families map to current-sim features as follows.

### t4_staged_warmup_capability

Purpose:

```text
older warmup evidence differs before obstacle reveal;
current and recent windows should later be matched.
```

Hook config:

```text
warmup_gate.enabled = true
obstacle.enabled = true
obstacle.perception_reveal_step = reveal_step
randomization varies mu/brake_scale or related capability pair
obstacle_relative_velocity_mode = "zero"
history_length = 1 for P0 online-GRU actor contract
```

Required diagnostics:

```text
warmup_gate_visible_steps
warmup_gate_clearance_margin
response history distance over older warmup window
current/recent distance placeholders for later rollout probe
```

### t4_capability_step_temporal

Purpose:

```text
capability change or response evidence appears before the decision point.
```

Hook config:

```text
friction_step.enabled = true
obstacle.enabled = true
obstacle.min_time_after_friction_step > 0
obstacle.perception_reveal_step = reveal_step
randomization varies drive/brake/tire stiffness pairs through fixed ranges
```

Required diagnostics:

```text
friction_step_at
friction_step_applied_by_decision
time_after_friction_step
older response distance
```

### t4_actuator_delay_response

Purpose:

```text
older command-response latency differs while current scene is matched.
```

Hook config:

```text
randomization varies steer_tau_scale and drive_tau_scale
warmup_gate.enabled may be true for controlled command-response evidence
obstacle.enabled = true
obstacle.perception_reveal_step = reveal_step
```

Required diagnostics:

```text
steer command/state lag
drive/brake actuator response lag
older response distance
action divergence placeholder
```

### t5_near_boundary_warmup

Purpose:

```text
normal history is near a terminal safety boundary;
wrong/reset/delayed/current-tiled history should reduce margin.
```

Hook config:

```text
warmup_gate.enabled = true
obstacle.enabled = true
obstacle.finish_on_pass = true
obstacle.clearance_margin_reward_scale may remain zero for no-training probes
obstacle ranges are tight near boundary
```

Required diagnostics:

```text
normal_margin
warmup_gate_clearance_margin
min_clearance_margin
terminal_reason
near_pass_margin band membership
```

### t5_high_speed_close_obstacle

Purpose:

```text
late reveal and high speed create narrow avoidance margin.
```

Hook config:

```text
speed_range high and narrow
obstacle.distance_range close and narrow
obstacle.perception_reveal_step or perception_reveal_distance constrains reveal
friction_step or low-mu randomization may be active
```

Required diagnostics:

```text
obstacle_distance at reveal
speed at reveal
min_clearance_margin
collision / obstacle_completed
```

### t5_boundary_axis_retarget

Purpose:

```text
retarget obstacle distance/lateral offset/half width or capability severity
until the result is near a terminal boundary.
```

Hook config:

```text
obstacle.enabled = true
finish_on_pass = true
retarget axes: obstacle distance, lateral offset, half width, capability scale
no private holdout and no actor-input changes
```

Required diagnostics:

```text
retarget_axis
retarget_value
bracket_lower/upper if later implemented
normal_margin
history-intervention margin placeholders
```

## Artifact Contract

M1505 should write only metadata/config artifacts:

```text
hook_spec_rows.csv
hook_source_family_summary.csv
hook_guardrail_summary.csv
summary.json
```

The later rollout smoke should add, but M1505 should not yet require:

```text
trace_rows.csv
candidate_rows.csv
intervention_rows.csv
matching_summary.csv
```

Required summary flags:

```text
training_started: false
evaluation_started: false
simulator_rollout_started: false
replay_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
training_corpus_exported: false
labels_enter_actor_input: false
level3_self_id_claim_made: false
```

## Candidate Conversion

The later rollout probe should convert traces into
`DecisiveHistoryTaskCandidate` only after all of these are measured from
rollout data:

```text
current_distance
recent_window_distance
older_history_distance
normal_margin
action_divergence
intervention_margins
intervention_success
```

M1505 may produce candidate stubs for schema tests, but stubs must be labeled
as `candidate_materialized: false` and must not be counted as simulator
candidates.

## Guardrail Logic

The hook layer may use privileged values for sampling and labels. It may not:

```text
append privileged fields to actor observation;
change the P0 72-dim actor contract;
use obstacle_label or hidden capability as actor input;
use private holdout seeds;
export a training corpus;
promote a checkpoint;
run PPO or actor updates;
claim level3 self-identification.
```

The intended actor observation remains:

```text
ego/IMU-like response;
actuator state;
previous physical commands;
ego-frame road/free-space/obstacle geometry;
recurrent hidden state from command-response history.
```

## M1505 Implementation Scope

M1505 should implement:

```text
1. hook/spec dataclasses;
2. conversion from M1502 CandidateSourcePlan to hook specs;
3. env_config factory for all six source families;
4. CSV/JSON artifact writers;
5. source-family and guardrail summaries;
6. focused tests that verify no training/replay/PPO/promotion/private holdout.
```

M1505 should not run full simulator rollout. The first rollout smoke should be
a separate milestone after the hook layer is reviewable and test-covered.

## Failure Cases

If M1505 cannot map a source family to current sim without shortcuts, classify
it before continuing:

```text
scenario_sampling_failure:
  source family cannot be represented in current sim honestly.

contract_violation:
  hook requires labels or hidden parameters in actor observation.

metric_artifact:
  hook produces metadata but cannot support measured current/recent/older
  history distances later.

lineage_invalid:
  implementation bypasses M1502/M1503 source-plan lineage.
```

## Next Route

Route to:

```text
m1505-paper-route-decisive-history-env-hook-implementation
```
