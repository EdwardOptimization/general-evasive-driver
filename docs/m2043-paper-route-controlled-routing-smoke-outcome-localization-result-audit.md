# M2043 Paper-Route Controlled Routing Smoke Outcome Localization Result Audit

- status: completed
- decision: `controlled_routing_smoke_outcome_localization_audit_route_to_task_quality_repair_design`
- audited summary: `runs/m2042_paper_route_controlled_routing_smoke_outcome_localization/summary.json`
- audited comparison candidates: `runs/m2042_paper_route_controlled_routing_smoke_outcome_localization/comparison_support_candidates.csv`
- audited offtrack dominance: `runs/m2042_paper_route_controlled_routing_smoke_outcome_localization/offtrack_dominance_slices.csv`
- reset/rollout/measured execution in M2043: `false`
- policy actions executed in M2043: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Result Audit

M2042 is a clean no-rerun localization pass:

```text
result_class: controlled_routing_smoke_outcome_localization_pass
episode_count: 432 / 432
profile_count: 12 / 12
spec_count: 36 / 36
family_count: 5 / 5
outcome_counts_match_source_summary: true
missing_schema_fields: []
all_selected_metrics_finite: true
guardrail_violation_count: 0
```

It reproduces the M2039 outcome counts exactly:

```text
success_obstacle_pass: 20
collision_failure: 13
off_track_noncollision_noncompletion: 399
```

## Candidate Audit

M2042 found no supported comparison slice:

```text
comparison_ready_candidate_count: 0
comparison_support_candidate_count: 0
```

This blocks:

```text
controller-family ranking;
finite-window-vs-GRU conclusion;
paper-level benchmark table;
using generated T2/T3 smoke proxies as paper-valid generated tasks;
level3 self-identification claim.
```

## Offtrack Audit

The failure mode is broad offtrack dominance, not collision dominance:

```text
offtrack_dominance_slice_count: 138
collision_dominance_slice_count: 0
```

Profile-level localization:

```text
L0_current_masked: 0/36 success, 4/36 collision, 32/36 offtrack
L1_one_step: 4/36 success, 2/36 collision, 30/36 offtrack
all L2 finite-window profiles: 0/36 success, 36/36 offtrack
L3_online_gru: 8/36 success, 4/36 collision, 24/36 offtrack
L3_reset_control_corrected: 8/36 success, 3/36 collision, 25/36 offtrack
```

Family-level localization:

```text
T1_reactive_active_safety: 3/48 success, 43/48 offtrack
T2_same_current_different_older_history: 7/120 success, 109/120 offtrack
T3_active_diagnostic_warmup: 5/120 success, 113/120 offtrack
T4_variable_diagnostic_delay: 1/48 success, 46/48 offtrack
T5_source_rich_extreme_dynamics: 4/96 success, 88/96 offtrack
```

Generated proxy split does not isolate the issue:

```text
original/smoke_proxy rows: 14/288 success, 265/288 offtrack
generated/smoke_proxy rows: 6/144 success, 134/144 offtrack
```

## Failure Taxonomy

Primary failure type:

```text
scenario_sampling_failure
```

Interpretation:

- The runner and localizer are not the active blocker.
- M2042 does not show a narrow slice suitable for candidate qualification.
- The measured panel is too hard or offtrack-biased across profiles, families,
  and generated/original source groups.
- The correct next step is a task-quality repair design, not ranking and not
  another localization pass over the same artifact.

## Route Decision

Selected next route:

```text
route_to_controlled_routing_smoke_task_quality_repair_design
```

M2044 should design a no-rollout repair wave from the M2042 localization:

```text
repair broad offtrack dominance before any ranking;
preserve generated rows as smoke_proxy unless separately validated;
avoid profile-specific tuning;
avoid weakening claim boundaries;
target source/task-quality changes, not controller-family ranking.
```

Rejected routes:

```text
direct controller-family ranking:
  rejected because comparison-ready and candidate-support counts are both 0.

candidate qualification:
  rejected because there are no candidate-support slices.

another no-rerun localization:
  rejected because M2042 already localizes the blocker broadly enough.

new measured rollout:
  rejected until task-quality repair is designed.
```

Controller ranking, finite-window-vs-GRU, paper-level comparison, and level3
self-ID claims remain blocked.
