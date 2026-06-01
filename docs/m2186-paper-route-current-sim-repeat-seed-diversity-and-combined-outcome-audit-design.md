# M2186 Paper-Route Current-Sim Repeat Seed-Diversity and Combined-Outcome Audit Design

- status: completed
- decision: `current_sim_repeat_seed_diversity_combined_outcome_audit_design_admit_implementation`
- manifest: `experiments/manifests/m2186-paper-route-current-sim-repeat-seed-diversity-and-combined-outcome-audit-design.json`
- training in M2186: `false`
- measured execution in M2186: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Purpose

M2184 produced complete two-repeat measured execution, but M2185 blocks
comparison because:

```text
M2184 is offtrack-dominated:
  100 success;
  36 collision;
  504 offtrack noncollision noncompletion.

repeat_1_seed_21761 and repeat_2_seed_21762 have identical top-level aggregate
values:
  success_rate 0.15625;
  collision_rate 0.05625;
  mean clearance / return / steps equal at aggregate precision.
```

M2186 freezes a no-rerun audit to decide whether M2174 + M2184 are
comparison-ready or whether the route should pivot to support repair or repeat
seed-diversity repair.

## Audit Inputs

M2187 should read:

```text
runs/m2174_paper_route_current_sim_controlled_comparison_measured_execution/summary.json
runs/m2174_paper_route_current_sim_controlled_comparison_measured_execution/episode_rows.csv
runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/materialized_workload.csv
runs/m2184_paper_route_current_sim_repeat_measured_execution/summary.json
runs/m2184_paper_route_current_sim_repeat_measured_execution/episode_rows.csv
runs/m2177_paper_route_current_sim_training_seed_repeat_materialization/combined_new_repeat_materialized_workload.csv
```

Normalize repeat identities:

```text
M2174 rows -> training_repeat_id = repeat_0_existing
M2184 rows -> use existing training_repeat_id
```

Expected combined panel:

```text
repeat groups: 3
episodes per repeat: 320
combined episodes: 960
task specs: 40
profiles: 8
```

## Required Audit Artifacts

M2187 should write:

```text
runs/m2187_paper_route_current_sim_repeat_seed_diversity_combined_outcome_audit/summary.json
runs/m2187_paper_route_current_sim_repeat_seed_diversity_combined_outcome_audit/combined_repeat_aggregate.csv
runs/m2187_paper_route_current_sim_repeat_seed_diversity_combined_outcome_audit/profile_repeat_outcome_aggregate.csv
runs/m2187_paper_route_current_sim_repeat_seed_diversity_combined_outcome_audit/repeat_diversity_flags.csv
runs/m2187_paper_route_current_sim_repeat_seed_diversity_combined_outcome_audit/comparison_readiness_claim_boundary.csv
```

## Checks

Completeness checks:

```text
episode_count == 960
repeat_count == 3
episodes_per_repeat == 320 for each repeat
metadata_missing_count == 0 for M2184 repeat rows
guardrail_violation_count == 0 for both M2174 and M2184
```

Outcome-support checks:

```text
combined_success_count
combined_collision_count
combined_offtrack_count
combined_success_rate
combined_offtrack_rate
per_repeat_success_count
per_repeat_offtrack_count
per_profile_success_count
```

Comparison should remain blocked if:

```text
combined_success_count < 240
or combined_offtrack_rate > 0.60
or any repeat success_count < 80
```

These thresholds are not paper claims; they are conservative readiness gates to
avoid comparing controller families on mostly failed/offtrack episodes.

Seed-diversity checks:

```text
compare repeat-level aggregate vectors;
compare per-profile outcome vectors between repeat_1 and repeat_2;
compare checkpoint path/hash identity across repeat_1 and repeat_2 where paths are available;
flag exact aggregate equality as seed_diversity_suspicious, not as ranking evidence.
```

The audit should distinguish:

```text
execution_complete_but_not_comparison_ready;
outcome_support_low_offtrack_dominated;
seed_diversity_suspicious;
seed_diversity_invalid;
comparison_ready_for_later_ranking_design.
```

## Claim Boundary

M2187 may only claim whether the combined repeat artifact is audit-clean,
support-sufficient, and seed-diverse enough to admit later comparison design.

M2187 must not:

```text
rank profiles;
select a winner;
make finite-window vs GRU verdicts;
claim paper-level benchmark evidence;
claim level3 self-identification.
```

## Next Step

M2187 may implement and run the no-rerun audit. No new measured execution is
allowed in M2187.
