# M2724 Engineering Controller Route A Current-M1690 Exact-Executable Reentry Offtrack Repair Design Preflight

## Metadata

- status: completed
- decision: `admit_current_m1690_exact_executable_reentry_offtrack_repair_candidate_materialization`
- manifest: `experiments/manifests/m2724-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-design-preflight.json`
- design doc: `docs/m2724-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-design-preflight.md`
- parent synthesis: `docs/m2723-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-branch-synthesis.md`
- parent target panel: `runs/m2721_engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_target_panel/summary.json`
- follow-up manifest: `experiments/manifests/m2725-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-candidate-materialization-preflight.json`
- next: `m2725-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-candidate-materialization-preflight`

## Design Premise

M2723 admits design, not execution. The accepted Route A target branch exposes:

```text
offtrack target rows: 31
  T4: 19
  T5: 12
  L0_current_masked: 8
  L2_window_50_current_tiled: 9
  L3_online_gru: 9
  L3_reset_control_corrected: 5

collision caution rows: 2
diagnostic success context rows: 3
protected exclusion rows: 12
```

Every offtrack target row is admitted only for repair planning:

```text
target_panel_admitted: true
execution_scheduled: false
target_labels_actor_visible: false
profile_ranking_allowed: false
```

The design therefore targets road containment and post-avoidance recovery while
keeping collision and protected rows as guardrails. It must not tune a single
profile, select a winner, widen geometry to hide offtrack, or add actor-visible
labels.

## Rejected Shortcuts

The repair must not use these as primary levers:

```text
change actor observation shape or action shape
add hidden dynamics, oracle labels, TTC, required clearance, path error, or success labels
make target/profile/protected labels actor-visible
widen track_width or move obstacles only to make rows easier
drop T4/T5 target rows
drop collision caution rows
drop diagnostic success context rows
drop protected exclusions
profile-specific tuning
rank profiles or controller families
execute reset, step, rollout, replay, training, PPO, validation, or private holdout
claim repair success, driver performance, current-sim verdict, paper evidence, high-fidelity result, or self-ID
```

## Repair Design

M2725 should materialize an artifact-only candidate repair pack. It should not
change active configs and should not execute the environment. The candidate pack
should bind each repair row back to the M2721 target panel.

The shared repair overlay should use existing `DriftEnvConfig` and
`ObstacleTaskConfig` fields rather than adding actor inputs:

```text
track_cost_scale: 2.8
heading_cost_scale: 0.25
road_margin_cost_scale: 1.2
road_margin_warning_fraction: 0.65
off_track_penalty: 6.0
termination_penalty: 8.0
obstacle.collision_penalty: 25.0
obstacle.dense_clearance_margin_reward_scale: 0.5
obstacle.dense_clearance_margin_reward_window: 10.0
obstacle.dense_clearance_margin_reward_clip: 0.25
obstacle.clearance_margin_reward_scale: 1.0
obstacle.clearance_margin_reward_clip: 0.25
obstacle.stable_aes_sideslip_penalty: preserve current value unless already configured
track_width: preserve parent value
obstacle distance and half-width: preserve parent value
```

The design intent is:

```text
road-margin pressure increases before offtrack termination
off_track termination receives a distinct penalty in addition to generic termination
clearance rewards and collision penalty remain explicit guardrails
geometry is not relaxed to manufacture success
the same overlay applies across profiles and target rows
```

M2725 should write candidate rows with at least these logical groups:

```text
source target rows:
  one row per M2721 offtrack target row
  includes task_family, profile_name, workload_id, task_source_id, and target_panel row id

shared repair overlay rows:
  one shared road-containment overlay
  one shared clearance/collision guardrail overlay
  no profile-specific hyperparameter override

guardrail rows:
  collision caution rows must be referenced as non-target guardrails
  diagnostic success rows must be referenced as context not winner evidence
  protected exclusions must remain not targets, not executed, and outside denominators
  actor 72/action 3 and no hidden/oracle input must be preserved

claim rows:
  design/materialization claims allowed
  repair success, validation, performance, ranking, current-sim, paper, high-fidelity, full-driver, and self-ID claims blocked
```

## Admission Gates For Later Execution

M2724 does not admit execution. A later execution-design route can be admitted
only after M2725 materializes a complete candidate pack and a result audit
accepts it.

Minimum admission gates for any later bounded repair execution design:

```text
all 31 offtrack target rows accounted
0 target rows dropped without visible rejection reason
2 collision caution rows present as guardrails
3 diagnostic success rows present as context
12 protected exclusion rows present and outside denominators
actor observation shape remains 72
action shape remains 3
hidden_oracle_actor_input_detected is false
target labels actor-visible is false
active config overwritten is false
repair_execution_started is false in materialization
training_started is false in materialization
ranking_admissible is false
winner_selected is false
```

If M2725 cannot satisfy these gates, the branch should route to repair-design
revision or stop rather than forcing execution.

## Follow-Up

M2724 admits artifact-only repair candidate materialization:

```text
m2725-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-candidate-materialization-preflight
```

M2725 should materialize:

```text
runs/m2725_engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_candidate_materialization/summary.json
candidate_target_rows.csv
shared_repair_overlay_rows.csv
guardrail_rows.csv
actor_contract_rows.csv
claim_boundary_rows.csv
gate_matrix.csv
docs/m2725-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-candidate-materialization-preflight.md
```

It must not run reset, step, rollout, replay, validation, training, PPO,
private holdout, profile ranking, winner selection, checkpoint promotion, or
success-rate verdict computation.

## Claim Boundary

Allowed M2724 claim:

```text
M2724 freezes a bounded offtrack repair design over the accepted M2721 target
panel and admits artifact-only candidate materialization before any execution.
```

Rejected claims:

```text
repair success
driver performance
validation readiness or result
controller-family ranking
winner selection
checkpoint promotion
success-rate verdict
paper evidence
finite-window-vs-GRU conclusion
current-response sufficiency
current-sim verdict
high-fidelity validation readiness or result
protected mitigation preservation result
full ideal driver completion
level3 self-identification
```
