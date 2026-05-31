# M2040 Paper-Route Controlled Routing Smoke Measured Execution Result Audit

- status: completed
- decision: `controlled_routing_smoke_measured_execution_audit_route_to_no_rerun_outcome_localization`
- manifest: `experiments/manifests/m2040-paper-route-controlled-routing-smoke-measured-execution-result-audit.json`
- audited summary: `runs/m2039_paper_route_controlled_routing_smoke_measured_execution/summary.json`
- audited episode rows: `runs/m2039_paper_route_controlled_routing_smoke_measured_execution/episode_rows.csv`
- measured execution in M2040: `false`
- rollout/policy actions in M2040: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Completeness Audit

M2039 is a clean measured execution pass:

```text
result_class=controlled_routing_smoke_measured_execution_pass
episode_count=432
target_episode_count=432
failure_count=0
spec_count=36
target_spec_count=36
profile_count=12
target_profile_count=12
metadata_missing_count=0
metric_completeness_failure_count=0
guardrail_violation_count=0
```

The run is therefore valid measured rollout data for the controlled
routing-smoke smoke panel.

## Outcome Audit

The raw outcomes are not ranking-ready:

```text
success_obstacle_pass: 20 / 432
collision_failure: 13 / 432
off_track_noncollision_noncompletion: 399 / 432
success_rate: 0.046296
collision_rate: 0.030093
clearance_margin_mean: 10.530665
```

Profile-level support:

```text
L3_online_gru: 8 / 36 success
L3_reset_control_corrected: 8 / 36 success
L1_one_step: 4 / 36 success
all L2 finite-window profiles: 0 / 36 success each
L0_current_masked: 0 / 36 success
```

This is useful signal, but it is not enough for controller-family ranking. The
panel is dominated by offtrack outcomes, and the successful rows are sparse.
Ranking directly from this table would mostly rank offtrack/task-quality
failure modes, not robust controller capability.

## Decision

Do not rank controller families yet.

Route next through the required branch synthesis gate, then to a no-rerun
outcome localization pass over M2039 artifacts if the synthesis decision keeps
that route. The localizer should answer:

```text
Which task families/source kinds/proxy templates generate the 20 successes?
Are successes concentrated in a few source rows or spread across sources?
Do L3 successes overlap with L1 successes or represent distinct slices?
Are failures dominated by particular families, generated proxies, or profiles?
Is there any comparison-ready slice with enough outcome support?
What repair/localization route should follow before paper comparison?
```

## Rejected Routes

Rejected now:

```text
controller-family ranking;
finite-window-vs-GRU conclusion;
paper-level benchmark table;
claiming generated T2/T3 rows are paper-valid;
new rollout before localizing existing outcomes.
```

## Next

M2041 should synthesize the M2031-M2040 routing-smoke branch because the
workflow cadence has fired. If it chooses to continue/pivot to localization,
M2042 should implement and run no-rerun outcome localization over:

```text
runs/m2039_paper_route_controlled_routing_smoke_measured_execution/episode_rows.csv
runs/m2039_paper_route_controlled_routing_smoke_measured_execution/summary.json
```

No new environment rollout should occur in M2041.
