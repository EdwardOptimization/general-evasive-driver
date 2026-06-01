# M2188 Paper-Route Current-Sim Repeat Seed-Diversity and Combined-Outcome Audit Result Audit

- status: completed
- decision: `current_sim_repeat_data_quality_audit_route_to_task_quality_offtrack_support_repair_design`
- manifest: `experiments/manifests/m2188-paper-route-current-sim-repeat-seed-diversity-and-combined-outcome-audit-result-audit.json`
- audited summary: `runs/m2187_paper_route_current_sim_repeat_seed_diversity_combined_outcome_audit/summary.json`
- training in M2188: `false`
- measured execution in M2188: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Audit Result

M2187 is accepted as a clean no-rerun audit of the combined M2174 + M2184
repeat panel.

The combined panel is complete:

```text
combined_episode_count: 960
repeat_count: 3
repeat_counts:
  repeat_0_existing: 320
  repeat_1_seed_21761: 320
  repeat_2_seed_21762: 320
completeness_pass: true
```

But it is not comparison-ready:

```text
combined_success_count: 163
combined_offtrack_count: 741
combined_success_rate: 0.16979166666666667
combined_offtrack_rate: 0.771875
per_repeat_success_min: 50
outcome_support_pass: false
comparison_ready: false
```

The readiness gates were:

```text
min_combined_success_count: 240
max_combined_offtrack_rate: 0.60
min_success_count_per_repeat: 80
```

Seed-diversity finding:

```text
checkpoint_duplicate_count: 0
repeat_aggregate_equal: true
profile_vector_equal: true
seed_diversity_status: suspicious_identical_repeat_outcome_vectors
```

Interpretation:

```text
Seed diversity is suspicious but not proven invalid: repeat_1 and repeat_2
checkpoints are not hash-duplicates, yet their aggregate and profile-level
outcome vectors are identical. This blocks ranking and should be rechecked
after support repair, but it is not the primary blocker.
```

## Decision

Do not rank profiles.

Do not claim finite-window vs GRU.

Do not treat the current repeat panel as paper-level benchmark evidence.

Primary blocker:

```text
outcome_support_low_offtrack_dominated
```

Secondary blocker:

```text
seed_diversity_suspicious_identical_repeat_outcome_vectors
```

Next route:

```text
Design a current-sim task-quality/offtrack support repair branch before any
controller-family comparison.
```

The repair should improve scenario support and reduce offtrack dominance while
preserving human-view/no-oracle actor contracts and measured-runner metadata
discipline. Seed diversity should remain a required audit after the repaired
panel produces enough support.

## Claim Boundary

Allowed claim:

```text
The current repeat panel is complete but not comparison-ready; repair is needed
before ranking or paper-level comparison.
```

Still blocked:

```text
profile ranking;
winner selection;
finite-window vs GRU verdict;
paper-level benchmark evidence;
level3 self-identification.
```

## Next Step

M2189 should design the task-quality/offtrack support repair. It should not run
new rollout or rank profiles.
