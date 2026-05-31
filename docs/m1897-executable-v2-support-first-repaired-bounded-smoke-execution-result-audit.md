# M1897 Executable V2 Support-First Repaired Bounded-Smoke Execution Result Audit

- status: completed
- decision: `support_first_repaired_smoke_audit_blocks_ranking_routes_to_clearance_containment_localization`
- audited summary: `runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/summary.json`
- audited episode rows: `runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/episode_rows.csv`
- reset/rollout in M1897: false
- measured execution in M1897: false
- training/replay/PPO: false
- controller-family ranking claim made: false
- paper-level claim made: false
- level3 self-ID claim made: false

## Execution Integrity

M1895 executed the exact repaired bounded-smoke workload cleanly:

```text
result_class: executable_v2_support_first_repaired_bounded_smoke_execution_pass
rollout_episode_count: 576 / 576
import_episode_count: 384 / 384
total_panel_row_count: 960 / 960
failure_count: 0
import_failure_count: 0
source_episode_join_missing_count: 0
controller_profile_count: 12 / 12
selected_source_spec_count: 16 / 16
repaired_executable_spec_count: 48 / 48
role_panel_count: 4 / 4
role_surface_count: 8 / 8
repair_variant_count: 5 / 5
metric_completeness_passed: true
metric_completeness_failure_count: 0
all_selected_metrics_finite: true
guardrail_violation_count: 0
```

Guardrails remain clean:

```text
training_started: false
replay_started: false
ppo_used: false
private_holdout_used: false
promoted: false
actor_input_contract_changed: false
profile_specific_tuning: false
controller_family_ranking_claim_made: false
paper_level_claim_made: false
level3_self_id_claim_made: false
```

So this is not an execution or artifact-integrity failure. The completed panel
is valid diagnostic evidence.

## Outcome Audit

The repaired smoke panel still has zero binary success:

```text
success: 0 / 960
collision_failure: 176 / 960
off_track_noncollision_noncompletion: 784 / 960
max_steps_noncompletion: 0 / 960
safe_noncollision_noncompletion: 0 / 960
```

The repaired variants do not create any successful cell:

```text
original: 0 / 192 success
semantics_only: 0 / 192 success
finish_extended: 0 / 192 success
road_relaxed: 0 / 192 success
road_relaxed_finish_extended: 0 / 192 success
```

The important finding is the clearance/containment conflict. Across all 960
rows:

```text
obstacle_clearance_pass=True,  road_containment_pass=False, collision_failure=False: 784
obstacle_clearance_pass=False, road_containment_pass=True,  collision_failure=True: 169
obstacle_clearance_pass=False, road_containment_pass=False, collision_failure=True: 7
obstacle_clearance_pass=True,  road_containment_pass=True: 0
```

This means the repaired task is not yet an interpretable controller-family
comparison. Rows mostly split into two incompatible outcomes:

- avoid the obstacle but leave the road;
- stay contained until collision.

No row currently demonstrates the desired simultaneous condition:

```text
clear obstacle AND stay contained AND complete/recover
```

## Slice Facts

The conflict is broad across roles:

```text
stable_aeb:
  obstacle_clearance_pass: 0.958
  road_containment_pass: 0.042
  collision_failure: 0.042

stable_aes_only:
  obstacle_clearance_pass: 0.983
  road_containment_pass: 0.013
  collision_failure: 0.017

drift_required_recovery:
  obstacle_clearance_pass: 0.750
  road_containment_pass: 0.250
  collision_failure: 0.250

unavoidable_mitigation:
  obstacle_clearance_pass: 0.575
  road_containment_pass: 0.400
  collision_failure: 0.425
```

It is also broad across controller profiles:

```text
all 12 profiles: 0.0 success_obstacle_pass_rate
best road-containment profile: L3_online_gru, road_containment_pass 0.2125
worst road-containment profile: L2_window_100_current_tiled, road_containment_pass 0.1500
```

These numbers are diagnostic only. They are not controller ranking, because the
primary success metric is saturated at zero and the failure mode is task-quality
dominated.

## Interpretation

M1895 improved execution infrastructure and produced complete evidence, but it
does not establish an interpretable repaired task-quality panel. The result is
not a driver-performance conclusion and not evidence for or against finite
window, current response, GRU, or self-identification.

The current blocker is sharper than the earlier diffuse zero-success finding:

```text
the repaired smoke panel has a disjoint obstacle-clearance / road-containment
failure surface.
```

The next research step should localize this conflict before any further repair
or ranking. Specifically, the project needs to identify whether the disjoint
surface is dominated by road width, obstacle lateral placement, obstacle timing,
role semantics, source family, or controller profile interactions.

## Decision

Controller-family ranking remains blocked.

Paper-level claims and level3 self-identification claims remain blocked.

Route to:

```text
m1898-executable-v2-support-first-clearance-containment-conflict-localization-design
```

M1898 should design a no-rollout localization pass over M1895 artifacts. It
should produce explicit conflict slices for:

- clearance-only rows;
- containment-but-collision rows;
- collision-and-off-track rows;
- any near-miss rows that almost satisfy both obstacle clearance and road
  containment.

No rollout, training, PPO, private holdout, controller ranking, or actor-input
change should occur before that localization design is complete.
