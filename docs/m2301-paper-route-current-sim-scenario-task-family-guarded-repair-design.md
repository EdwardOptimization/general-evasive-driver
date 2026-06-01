# M2301 Paper-Route Current-Sim Scenario Task-Family Guarded-Repair Design

- status: completed
- decision: `guarded_repair_design_admit_config_materialization`
- manifest: `experiments/manifests/m2301-paper-route-current-sim-scenario-task-family-guarded-repair-design.json`
- parent synthesis: `docs/m2300-paper-route-current-sim-scenario-task-family-guarded-repair-branch-synthesis.md`
- parent gate spec: `runs/m2298_paper_route_current_sim_scenario_task_family_offtrack_primary_collision_guardrail/repair_gate_spec.json`
- reset/rollout/policy action in M2301: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Design Decision

M2301 admits a bounded config-materialization implementation:

```text
m2302-paper-route-current-sim-scenario-task-family-guarded-repair-config-materialization
```

M2302 should not train. It should materialize a shared guarded-repair config
matrix that a later execution milestone can train and evaluate.

## Repair Premise

M2293/M2295 show a broad offtrack failure, not a reset or metadata failure:

```text
global success_rate: 0.06388888888888888
global offtrack_rate: 0.7268518518518519
global collision_rate: 0.1935185185185185
dominant_failure_mode: offtrack_dominated_failure
```

M2298/M2299 turn that into the accepted repair gate:

```text
offtrack_target_slice_count: 20
collision_guardrail_slice_count: 11
profile_target_slice_count: 0
profile_guardrail_slice_count: 0
```

Therefore the next repair should not widen the track, change scenario specs, or
tune profile-specific knobs. It should materialize one shared containment
training config family and judge it later by M2298 gates.

## Allowed Repair Knobs

M2302 may change only shared reward/config knobs already supported by the
current simulator:

```text
track_cost_scale: 3.4
heading_cost_scale: 0.35
road_margin_cost_scale: 3.4
road_margin_warning_fraction: 0.45
off_track_penalty: 10.0
termination_penalty: 8.0
dense_clearance_margin_reward_scale: 0.5
dense_clearance_margin_reward_window: 10.0
clearance_margin_reward_scale: 1.0
clearance_margin_reward_clip: 0.25
collision_penalty: 25.0
```

These are shared guarded-v2 values, not profile-specific tuning. They increase
dense road-margin pressure relative to the M2262 source configs while keeping
the scenario and actor contract fixed. Return improvement is insufficient.
Later repair must be judged by offtrack targets and collision guardrails.

## Fixed Boundary

M2302 must keep:

```text
source_config_root:
  runs/m2262_paper_route_current_sim_midcourse_corridor_containment_training_execution/configs

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

config_count: 15
profile_count: 5
seed_count: 3
budget_signature_count: 1
track_width_widened: 0
actor_contract_violation_count: 0
profile_specific_tuning_count: 0
ranking_admissible_count: 0
```

Do not change scenario specs or profile definitions. M2302 can write training
commands, but it must not execute them.

## Later Acceptance Gates

The later training and measured-execution route must pass these gates before
any comparison or ranking:

```text
completeness:
  episode_count: 1080 / 1080
  metadata_missing_count: 0
  metric_completeness_failure_count: 0
  guardrail_violation_count: 0

offtrack target:
  global offtrack_count decreases vs M2293
  offtrack_count on each M2298 target slice decreases or holds

collision guardrail:
  global collision_count does not increase vs M2293
  collision_count on each M2298 guardrail slice does not increase

claim boundary:
  ranking_admissible_count: 0
  winner_selected: false
  paper_level_claim_made: false
  finite_window_vs_gru_conclusion_made: false
  level3_self_id_claim_made: false
```

If offtrack decreases only because collision increases, the repair fails.

## Blocked Shortcuts

M2301 blocks:

- widening `track_width`;
- changing obstacle placement, labels, or scenario specs;
- profile-specific reward tuning;
- selecting a profile winner;
- comparing finite-window vs GRU;
- using this repair as self-ID evidence;
- claiming paper-level benchmark readiness.

## Follow-Up

Pre-register:

```text
experiments/manifests/m2302-paper-route-current-sim-scenario-task-family-guarded-repair-config-materialization.json
```

M2302 should implement and run only the config materializer. It should write the
config pack, matrix, copied gate spec, claim-boundary file, and summary. It
should not run reset, rollout, policy action, training, replay, PPO, private
holdout, ranking, or paper/self-ID evaluation.
