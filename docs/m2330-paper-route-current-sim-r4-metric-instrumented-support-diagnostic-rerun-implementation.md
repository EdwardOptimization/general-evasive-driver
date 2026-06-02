# M2330 Paper-Route Current-Sim R4 Metric-Instrumented Support Diagnostic Rerun Implementation

- status: completed
- result_class: `current_sim_r4_metric_instrumented_support_diagnostic_rerun_pass`
- manifest: `experiments/manifests/m2330-paper-route-current-sim-r4-metric-instrumented-support-diagnostic-rerun-implementation.json`
- implementation: `src/autodrift/paper_route_current_sim_r4_metric_instrumented_support_diagnostic_rerun.py`
- tests: `tests/test_paper_route_current_sim_r4_metric_instrumented_support_diagnostic_rerun.py`
- summary: `runs/m2330_paper_route_current_sim_r4_metric_instrumented_support_diagnostic_rerun/summary.json`
- reset/rollout/policy action: `true`
- measured execution: `true`
- training/replay/PPO: `false`
- support-policy ranking claim made: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Command

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_r4_metric_instrumented_support_diagnostic_rerun \
  --base-config configs/paper_route_current_sim_scenario_task_family_v0.json \
  --output-dir runs/m2330_paper_route_current_sim_r4_metric_instrumented_support_diagnostic_rerun \
  --target-scenario-spec-count 12 \
  --target-support-policy-count 3 \
  --seed-repeats 5 \
  --target-episode-count 180 \
  --next-blocker m2331-paper-route-current-sim-r4-metric-instrumented-support-diagnostic-rerun-result-audit
```

## Implementation

M2330 adds a bounded wrapper around the existing support-policy feasibility
calibration runner:

```text
base config:
  configs/paper_route_current_sim_scenario_task_family_v0.json

materialized subset:
  runs/m2330_paper_route_current_sim_r4_metric_instrumented_support_diagnostic_rerun/r4_only_config.json

subset rule:
  role_family == R4_unavoidable_mitigation

support policies:
  aeb
  aes
  envelope_aes
```

The wrapper also writes:

```text
r4_metric_field_completeness.csv
```

This checks exported field presence and simple nonempty/finite counts without
fabricating unavailable post-collision metrics.

## Artifact Completeness

```text
scenario_spec_count: 12 / 12
support_policy_count: 3 / 3
seed_repeat_count: 5
episode_count: 180 / 180
failure_count: 0
validation_failure_count: 0
metadata_missing_count: 0
metric_completeness_failure_count: 0
non_r4_role_count: 0
guardrail_violation_count: 0
```

R4 scenario IDs:

```text
m2277_r4_00
m2277_r4_01
m2277_r4_02
m2277_r4_03
m2277_r4_04
m2277_r4_05
m2277_r4_06
m2277_r4_07
m2277_r4_08
m2277_r4_09
m2277_r4_10
m2277_r4_11
```

## Exported R4 Metric Fields

M2330 preserves all required R4 mitigation diagnostic fields in
`episode_rows.csv`:

```text
required_r4_export_field_count: 13
required_r4_export_missing_field_count: 0
r4_metric_field_completeness_rows: 13
```

Field completeness snapshot:

```text
impact_speed_mps: present, finite 173 / 180
impact_speed_mps_available: present, true 173 / 180
time_to_collision_s: present, finite 173 / 180
time_to_collision_s_available: present, true 173 / 180
collision_side_proxy: present, nonempty 173 / 180
delta_v_at_impact_mps_available: present, true 0 / 180
post_event_speed_mps_available: present, true 0 / 180
recoverability_window_success_available: present, true 0 / 180
impact_speed_proxy: present, finite 173 / 180
impact_beta_abs: present, finite 173 / 180
impact_yaw_rate_abs: present, finite 173 / 180
impact_severity_proxy: present, finite 173 / 180
collision_mitigation_score: present, finite 180 / 180
```

Unavailable post-collision fields remain availability-false. M2330 does not
change collision termination behavior.

## Diagnostic Outcome Snapshot

Global R4 support-policy diagnostic outcome:

```text
global_success_count: 0
global_collision_count: 173
global_offtrack_count: 6
global_obstacle_completed_count: 0

global_success_rate: 0.0
global_collision_rate: 0.9611111111111111
global_offtrack_rate: 0.03333333333333333
```

Outcome buckets:

```text
collision_failure: 173
off_track_noncollision_noncompletion: 6
max_steps_noncompletion: 1
```

Role support summary:

```text
R4_unavoidable_mitigation:
  scenario_count: 12
  support_clear_count: 0
  support_mixed_count: 3
  support_blocked_count: 9
  metric_conflict_count: 0
```

This is a support diagnostic result only. It does not rank `aeb`, `aes`, or
`envelope_aes`, and it does not select a winner.

## Claim Boundary

Allowed claim:

```text
M2330 produced fresh R4-only diagnostic support-policy rows with exported
mitigation metric fields and zero guardrail violations.
```

Blocked claims:

```text
support policies ranked;
controller families ranked;
R4 mitigation solved;
mitigation performance proven;
paper-level evidence;
finite-window vs GRU conclusion;
level3 self-identification evidence.
```

## Verification

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_current_sim_r4_metric_instrumented_support_diagnostic_rerun.py
```

Result:

```text
2 passed in 2.10s
```

## Follow-Up Manifest

```text
experiments/manifests/m2331-paper-route-current-sim-r4-metric-instrumented-support-diagnostic-rerun-result-audit.json
```

Next route:

```text
m2331-paper-route-current-sim-r4-metric-instrumented-support-diagnostic-rerun-result-audit
```
