# M2213 Paper-Route Current-Sim Offtrack-Support Outcome Localization Branch Synthesis

- status: completed
- decision: `current_sim_offtrack_support_localization_synthesis_pivot_to_support_slice_validity`
- synthesis decision: `pivot`
- synthesis window: `M2203-M2212`
- primary failure taxonomy: `scenario_sampling_failure`
- implementation in M2213: `false`
- reset in M2213: `false`
- measured execution in M2213: `false`
- policy actions executed in M2213: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Evidence Summary

M2203 froze the repaired 2304-cell measured-execution command. M2204 failed
closed before rollout because repeat metadata activation treated
`checkpoint_materialization_mode` as repeat identity. M2205-M2208 repaired and
audited that runner behavior:

```text
metadata_missing_rows after repair: 0
validation_failure_rows after repair: 0
focused tests: 4 passed
```

M2209 then reran the measured execution successfully:

```text
result_class: current_sim_controlled_comparison_measured_execution_pass
episode_count: 2304
failure_count: 0
metadata_missing_count: 0
metric_completeness_failure_count: 0
guardrail_violation_count: 0
success_obstacle_pass: 374
collision_failure: 49
off_track_noncollision_noncompletion: 1881
```

M2210 correctly rejected comparison readiness because the measured outcomes
were offtrack dominated:

```text
success_rate: 0.1623263888888889
collision_rate: 0.021267361111111112
offtrack_rate: 0.81640625
```

M2211 designed a no-rerun outcome localizer, and M2212 implemented it:

```text
group_row_count: 212
comparison_ready_candidate: 13
candidate_support: 27
offtrack_dominated: 112
low_sample_count: 60
guardrail_violation_count: 0
```

The strongest-looking support is diagnostic and concentrated around finite
window slices:

```text
profile_name=L2_window_25: 209 / 288 success
task_family=T1 x explicit_finite_window: 46 / 96 success
task_family=T2 x explicit_finite_window: 47 / 120 success
```

The broad panel remains blocked:

```text
overall: offtrack_dominated
history_representation=online_recurrent_hidden: 0 / 576 success
profile_level=L3: 0 / 576 success
T4 older-history ambiguity: offtrack_dominated
T5 terminal-boundary: offtrack_dominated
```

## Supported Claims

The branch now supports these limited claims:

```text
1. The repaired measured runner can execute the 2304-cell panel end-to-end.
2. Repeat metadata activation is now tied to repeat identity fields rather than
   checkpoint provenance fields.
3. M2209 outcomes are complete and metric-clean but offtrack dominated.
4. M2212 can localize support/blocker slices without rerun or ranking.
5. Some public diagnostic slices have enough support to deserve denominator
   validity audit.
```

## Falsified Claims

Falsified for this branch:

```text
1. The repaired 288-spec / 2304-cell panel is globally comparison-ready.
2. The M2209 aggregate can rank controller families.
3. The M2212 comparison-ready candidate labels are a finite-window-vs-GRU verdict.
4. Another blind offtrack-support repair is justified before auditing slice validity.
```

Still unsupported:

```text
paper-level benchmark result;
finite-window vs GRU conclusion;
level3 self-identification;
profile winner selection;
private-holdout generalization.
```

## Failure Taxonomy Summary

```text
metric_artifact:
  M2204 failed before rollout because repeat metadata activation was too broad.
  M2207 repaired the issue and M2208 audited it clean.

scenario_sampling_failure:
  M2209 executed cleanly but the outcome distribution remained broadly
  offtrack dominated.

none:
  M2212 localization itself passed with guardrail 0 and no rollout.
```

The active blocker is no longer runner infrastructure. It is whether the
localized candidate slices contain denominator-backed comparison signal or are
only profile/history-axis artifacts.

## Public-Gate Overfit Risk

Risk is high if the project uses the 13 M2212 candidate slices to claim a
controller result:

```text
The panel is public and derived from repeated offtrack repairs.
The global denominator is still offtrack dominated.
The strongest candidate is a profile-containing slice.
The L3 online/recurrent profiles have zero success in this panel.
The localizer did not run history interventions or private holdouts.
```

The safe use of M2212 is as a blocker map, not as a comparison table.

## Actual Capability Change

The branch changed the project capability from:

```text
checkpoint-complete measured-execution readiness
```

to:

```text
complete repaired measured execution plus no-rerun outcome-support localization
```

This is useful evidence, but it still does not produce a paper comparison.

## Next Branch Decision

Selected:

```text
pivot:
  paper_route_current_sim_support_slice_validity
```

The next branch should audit the M2212 candidate slices before any new repair or
comparison claim. It should answer:

```text
1. Which candidate slices are scene-backed rather than profile-only artifacts?
2. Which slices have comparable denominators across profile/history groups?
3. Are any candidate slices suitable for a bounded diagnostic comparison?
4. Do offtrack-dominated slices require task-quality repair, profile training
   repair, or abandonment as comparison evidence?
```

Rejected routes:

```text
direct controller-family ranking from M2209/M2212;
direct finite-window vs GRU conclusion;
another broad offtrack-support repair before slice validity audit;
high-fidelity simulator migration before current-sim route is decided;
self-ID claim from aggregate success/offtrack outcomes.
```

## Next

Next milestone:

```text
m2214-paper-route-current-sim-support-slice-validity-audit-design
```
