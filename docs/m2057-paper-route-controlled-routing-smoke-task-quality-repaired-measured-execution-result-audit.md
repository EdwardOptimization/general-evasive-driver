# M2057 Paper-Route Controlled Routing Smoke Task-Quality Repaired Measured Execution Result Audit

- status: completed
- decision: `controlled_routing_smoke_task_quality_repaired_measured_audit_route_to_branch_synthesis`
- failure taxonomy: `scenario_sampling_failure`
- audited summary: `runs/m2056_paper_route_controlled_routing_smoke_task_quality_repaired_measured_execution/summary.json`
- audited episode rows: `runs/m2056_paper_route_controlled_routing_smoke_task_quality_repaired_measured_execution/episode_rows.csv`
- measured execution in M2057: `false`
- rollout/policy actions in M2057: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Completeness Audit

M2056 is a clean measured-execution pass:

```text
result_class: controlled_routing_smoke_measured_execution_pass
episode_count: 2304 / 2304
failure_count: 0
spec_count: 192 / 192
profile_count: 12 / 12
metadata_missing_count: 0
metric_completeness_failure_count: 0
all_selected_metrics_finite: true
family_quota_pass: true
source_kind_quota_pass: true
proxy_template_quota_pass: true
generated_proxy_quota_pass: true
guardrail_violation_count: 0
```

The run is therefore valid measured rollout data for the repaired
routing-smoke smoke panel.

## Outcome Audit

The raw outcomes are not ranking-ready:

```text
success_obstacle_pass: 45 / 2304
collision_failure: 14 / 2304
off_track_noncollision_noncompletion: 2245 / 2304
success_rate: 0.019531
collision_rate: 0.006076
clearance_margin_mean: 16.725172
```

Profile-level support:

```text
L3_online_gru: 26 / 192 success
L3_reset_control_corrected: 17 / 192 success
L0_current_masked: 1 / 192 success
L1_one_step: 1 / 192 success
all L2 finite-window profiles and tiled controls: 0 success
```

Family-level success rates remain low:

```text
T1_reactive_active_safety: 10 / 384
T2_same_current_different_older_history: 12 / 768
T3_active_diagnostic_warmup: 11 / 684
T4_variable_diagnostic_delay: 5 / 216
T5_source_rich_extreme_dynamics: 7 / 252
```

This is useful signal, but it is not controller-family ranking evidence. The
panel is still dominated by road-departure failure modes. The repaired panel
expanded execution coverage, but it did not solve the active ranking blocker.

## Comparison Readiness

Rejected now:

```text
controller-family ranking;
finite-window-vs-GRU conclusion;
paper-level benchmark table;
claiming generated rows are paper-valid benchmark tasks;
level3 self-identification.
```

Reason:

```text
The measured table mostly ranks task/offtrack failure, not robust evasive-driver
capability. L3 has more successes than the current/finite-window profiles, but
support remains sparse and the smoke-proxy task semantics are not paper-valid.
```

## Failure Taxonomy

Primary failure type:

```text
scenario_sampling_failure
```

Interpretation:

- The runner and metadata path are no longer the active blocker.
- The reset-valid repaired panel can be executed completely.
- The repaired panel remains too offtrack-dominated for fair comparison.
- This repeats the earlier routing-smoke failure mode after a full repair path.

## Route Decision

Selected:

```text
route_to_branch_synthesis_before_more_local_repair
```

Do not immediately start another localization/repair loop. The local-search
guard for M2057 explicitly fires when the same offtrack-dominance failure
reappears. M2058 should synthesize the repaired measured-execution branch and
choose whether to:

```text
pivot to a broader task-distribution redesign;
build a smaller comparison-support slice only as bounded diagnostic evidence;
stop this routing-smoke panel as a ranking route;
or continue with no-rerun localization only if it changes the branch decision.
```

Rejected:

```text
direct no-rerun localization:
  rejected as the immediate next step because the repeated broad offtrack
  failure triggers synthesis first.

direct task-quality repair:
  rejected because another repair loop would risk local-search drift.

direct measured rerun:
  rejected because M2056 is already complete.

direct ranking:
  rejected because outcome support is sparse and offtrack dominated.
```

Controller ranking, finite-window-vs-GRU, paper-level comparison, and level3
self-ID claims remain blocked.

## Next

Next milestone:

```text
m2058-paper-route-controlled-routing-smoke-task-quality-repaired-measured-execution-synthesis
```
