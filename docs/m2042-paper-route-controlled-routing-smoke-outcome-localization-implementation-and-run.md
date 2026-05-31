# M2042 Paper-Route Controlled Routing Smoke Outcome Localization Implementation and Run

- status: completed
- decision: `controlled_routing_smoke_outcome_localization_pass_route_to_result_audit`
- result class: `controlled_routing_smoke_outcome_localization_pass`
- implementation: `src/autodrift/paper_route_controlled_routing_smoke_outcome_localization.py`
- focused tests: `3 passed`
- summary: `runs/m2042_paper_route_controlled_routing_smoke_outcome_localization/summary.json`
- reset/rollout/measured execution in M2042: `false`
- policy actions executed in M2042: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Result

The no-rerun localizer reproduced the M2039 measured outcome counts exactly:

```text
episode_count: 432 / 432
profile_count: 12 / 12
spec_count: 36 / 36
family_count: 5 / 5
outcome_counts_match_source_summary: true
missing_schema_fields: []
all_selected_metrics_finite: true
guardrail_violation_count: 0
```

Outcome counts:

```text
success_obstacle_pass: 20
collision_failure: 13
off_track_noncollision_noncompletion: 399
```

Generated proxy split:

```text
generated_source_row=false: 288 rows, 14 successes, 9 collisions, 265 offtrack
generated_source_row=true: 144 rows, 6 successes, 4 collisions, 134 offtrack
```

## Localization

The localizer wrote aggregate slices for:

```text
profile;
family;
source_kind;
proxy_template;
generated proxy;
sampled label;
profile x family;
profile x source_kind;
profile x generated proxy;
source x profile;
source x family x kind.
```

Key counts:

```text
success_rows: 20
comparison_ready_candidate_count: 0
comparison_support_candidate_count: 0
offtrack_dominance_slice_count: 138
collision_dominance_slice_count: 0
```

Profile localization:

```text
L3_online_gru: 8/36 success, 4/36 collision, 24/36 offtrack
L3_reset_control_corrected: 8/36 success, 3/36 collision, 25/36 offtrack
L1_one_step: 4/36 success, 2/36 collision, 30/36 offtrack
L0_current_masked: 0/36 success, 4/36 collision, 32/36 offtrack
all L2 finite-window profiles: 0/36 success, 36/36 offtrack
```

Family localization:

```text
T1_reactive_active_safety: 3/48 success, 2/48 collision, 43/48 offtrack
T2_same_current_different_older_history: 7/120 success, 4/120 collision, 109/120 offtrack
T3_active_diagnostic_warmup: 5/120 success, 2/120 collision, 113/120 offtrack
T4_variable_diagnostic_delay: 1/48 success, 1/48 collision, 46/48 offtrack
T5_source_rich_extreme_dynamics: 4/96 success, 4/96 collision, 88/96 offtrack
```

## Interpretation Boundary

M2042 is useful no-rerun localization evidence, but not a controller ranking.

Supported:

```text
M2039 outcome counts are reproducible from episode rows.
The active blocker is broad offtrack dominance, not missing metadata or
localizer schema failure.
No comparison-ready or candidate-support slices were found under the registered
support criteria.
```

Unsupported:

```text
controller-family ranking;
finite-window-vs-GRU conclusion;
paper-level generated-task validity;
level3 self-identification;
new training or repair effectiveness.
```

## Next

M2043 should audit this result before selecting task-quality repair, comparison
candidate qualification, or another synthesis route.
