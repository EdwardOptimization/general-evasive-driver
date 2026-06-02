# M2326 Paper-Route Current-Sim R4 Mitigation Metric Instrumentation Design

- status: completed
- result_class: `r4_mitigation_metric_instrumentation_design_admit_logging_field_implementation`
- manifest: `experiments/manifests/m2326-paper-route-current-sim-r4-mitigation-metric-instrumentation-design.json`
- parent audit: `docs/m2325-paper-route-current-sim-scenario-task-family-role-stratified-residual-redesign-result-audit.md`
- parent metric availability: `runs/m2324_paper_route_current_sim_scenario_task_family_role_stratified_residual_redesign/r4_mitigation_metric_availability.csv`
- reset/rollout/policy action in M2326: `false`
- training/replay/PPO in M2326: `false`
- actor input changed: `false`
- reward/training objective changed: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Code Inspection Result

The project already has logging-only outcome metric instrumentation:

```text
src/autodrift/outcome_metric_instrumentation.py
```

`evaluate.run_episode_with_policy` computes these fields from `step_infos` and
adds them to the episode row:

```text
impact_speed_proxy
impact_beta_abs
impact_yaw_rate_abs
impact_severity_proxy
collision_mitigation_score
recovery_success
first_recovery_time_s
controlled_drift_recovery_success
max_off_track_overshoot
time_to_first_off_track_s
off_track_severity_proxy
```

The M2324 gap appears because the scenario task-family measured/support runners
pre-create `episode_rows.csv` with a restricted `EPISODE_FIELDNAMES` list. The
existing `append_csv_row(..., extrasaction="ignore")` then drops outcome metric
fields not listed in that header.

So the first implementation should be a logging/export fix, not a new model,
reward, actor input, or rollout policy.

## Required Field Mapping

M2326 maps the M2324 required fields as follows:

```text
impact_speed_mps:
  source: existing impact_speed_proxy from outcome_metric_instrumentation
  action: export canonical alias and keep proxy source

delta_v_at_impact_mps:
  source: unavailable in current sim collision model
  action: export NaN plus availability flag false; do not fabricate delta-v

time_to_collision_s:
  source: collision step/time from step_infos
  action: add logging-only field in outcome_metric_instrumentation

collision_angle_or_side:
  source: active_obstacle_body_x/y at collision can support a body-frame side proxy
  action: export collision_side_proxy; keep canonical side unavailable unless side semantics are validated

post_event_speed_mps:
  source: unavailable as true post-event metric because the current env terminates on collision
  action: export NaN plus availability flag false; optional terminal_speed_at_collision proxy may be logged separately

post_event_yaw_rate_abs:
  source: unavailable as true post-event metric because the current env terminates on collision
  action: export NaN plus availability flag false; optional terminal_yaw_rate_abs_at_collision proxy may be logged separately

post_event_offtrack_overshoot:
  source: unavailable as true post-event metric because the current env terminates on collision
  action: export NaN plus availability flag false; keep max_off_track_overshoot as proxy

recoverability_window_success:
  source: existing recovery_success applies after obstacle pass, not after collision
  action: export false/NaN availability for collision-terminated R4; future diagnostic continuation required for true post-collision recoverability
```

## M2327 Implementation Scope

M2327 should implement a bounded logging/export patch:

```text
1. Add canonical R4 metric alias fields and availability flags in outcome metric logging.
2. Extend scenario task-family measured execution EPISODE_FIELDNAMES.
3. Extend scenario task-family support-policy feasibility EPISODE_FIELDNAMES.
4. Add focused tests using stub rollout metrics; do not run real env rollout.
5. Keep actor input, reward, policy behavior, training, and ranking unchanged.
```

Expected canonical fields:

```text
impact_speed_mps
impact_speed_mps_available
delta_v_at_impact_mps
delta_v_at_impact_mps_available
time_to_collision_s
time_to_collision_s_available
collision_angle_or_side
collision_angle_or_side_available
collision_side_proxy
post_event_speed_mps
post_event_speed_mps_available
post_event_yaw_rate_abs
post_event_yaw_rate_abs_available
post_event_offtrack_overshoot
post_event_offtrack_overshoot_available
recoverability_window_success
recoverability_window_success_available
```

Expected existing proxy fields to preserve:

```text
impact_speed_proxy
impact_beta_abs
impact_yaw_rate_abs
impact_severity_proxy
collision_mitigation_score
recovery_success
first_recovery_time_s
controlled_drift_recovery_success
off_track_severity_proxy
```

## Non-Goals

M2327 must not:

```text
change actor observation;
add privileged fields to actor input;
change reward;
change termination behavior;
continue the simulation after collision;
run measured execution;
rank support policies or controller families;
claim mitigation performance.
```

Post-collision continuation may be a later diagnostic branch, but it is not the
M2327 implementation.

## Claim Boundary

Allowed claim:

```text
M2326 identifies the current logging/export cause of the R4 metric availability
gap and freezes a bounded field-export implementation route.
```

Blocked claims:

```text
mitigation performance measured;
post-collision recovery measured;
R4 solved;
support-policy/controller ranking;
paper-level evidence;
finite-window vs GRU conclusion;
level3 self-identification evidence.
```

## Follow-Up Manifest

```text
experiments/manifests/m2327-paper-route-current-sim-r4-mitigation-metric-instrumentation-implementation.json
```
