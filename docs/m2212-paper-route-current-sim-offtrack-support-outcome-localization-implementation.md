# M2212 Paper-Route Current-Sim Offtrack-Support Outcome Localization Implementation

- status: completed
- decision: `current_sim_offtrack_support_outcome_localization_pass_route_to_required_branch_synthesis`
- manifest: `experiments/manifests/m2212-paper-route-current-sim-offtrack-support-outcome-localization-implementation.json`
- implementation: `src/autodrift/paper_route_current_sim_offtrack_support_outcome_localization.py`
- tests: `tests/test_paper_route_current_sim_offtrack_support_outcome_localization.py`
- run artifact: `runs/m2212_paper_route_current_sim_offtrack_support_outcome_localization/summary.json`
- measured execution in M2212: `false`
- policy action executed in M2212: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Result

M2212 implemented and ran the no-rerun outcome localizer over the M2209 measured
episode rows.

```text
result_class: current_sim_offtrack_support_outcome_localization_pass
input_episode_count: 2304
parent_episode_count: 2304
group_row_count: 212
guardrail_violation_count: 0
```

Outcome support remained dominated by road-departure noncompletion:

```text
overall_success_rate: 0.1623263888888889
overall_collision_rate: 0.021267361111111112
overall_offtrack_rate: 0.81640625
```

Support labels:

```text
comparison_ready_candidate: 13
candidate_support: 27
offtrack_dominated: 112
low_sample_count: 60
collision_dominated: 0
low_success_support: 0
mixed_unresolved: 0
```

## Localization

The comparison-ready candidates are not a controller-family verdict. They are
diagnostic support slices, mostly concentrated around `L2_window_25` and
`explicit_finite_window` groups:

```text
profile_name=L2_window_25: 209 / 288 success
history_representation=explicit_finite_window on T1: 46 / 96 success
history_representation=explicit_finite_window on T2: 47 / 120 success
```

The broad panel is still not comparison-ready:

```text
overall: 374 / 2304 success, 1881 / 2304 offtrack
history_representation=online_recurrent_hidden: 0 / 576 success
profile_level=L3: 0 / 576 success
task_family=T4_same_current_different_older_history: offtrack_dominated
task_family=T5_terminal_boundary_near_constraint: offtrack_dominated
```

This result should not be used to rank profiles or conclude finite-window vs
GRU. It only says where support exists and where the panel remains blocked.

## Artifacts

M2212 writes:

```text
runs/m2212_paper_route_current_sim_offtrack_support_outcome_localization/summary.json
runs/m2212_paper_route_current_sim_offtrack_support_outcome_localization/group_outcome_support.csv
runs/m2212_paper_route_current_sim_offtrack_support_outcome_localization/comparison_ready_candidate_slices.csv
runs/m2212_paper_route_current_sim_offtrack_support_outcome_localization/offtrack_dominated_slices.csv
runs/m2212_paper_route_current_sim_offtrack_support_outcome_localization/collision_dominated_slices.csv
runs/m2212_paper_route_current_sim_offtrack_support_outcome_localization/low_success_support_slices.csv
runs/m2212_paper_route_current_sim_offtrack_support_outcome_localization/claim_boundary.csv
runs/m2212_paper_route_current_sim_offtrack_support_outcome_localization/run_state.json
```

## Validation

Focused test:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_paper_route_current_sim_offtrack_support_outcome_localization.py
2 passed
```

## Claim Boundary

Allowed claim:

```text
M2209 outcomes have been localized into support and blocker slices without
rerun, training, policy execution, profile ranking, or paper-level claims.
```

Still blocked:

```text
controller-family ranking;
winner selection;
finite-window vs GRU verdict;
paper-level benchmark result;
level3 self-identification;
profile promotion.
```

## Next Step

M2203-M2212 reached the workflow synthesis cadence, and M2212 still shows
offtrack-dominated global support. The next milestone is therefore a required
branch synthesis:

```text
m2213-paper-route-current-sim-offtrack-support-outcome-localization-branch-synthesis
```
