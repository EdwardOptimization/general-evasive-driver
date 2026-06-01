# M2127 Paper-Route Outcome-Supported Decisive Comparison-Support Outcome Localization Design

- status: completed
- decision: `comparison_support_outcome_localization_design_route_to_no_rerun_implementation`
- reset/rollout/measured execution in M2127: `false`
- policy actions executed in M2127: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Constraint

M2127 must not run another environment reset or rollout. It only designs a
no-rerun localization pass over M2125 artifacts.

The older controlled routing-smoke localizer has the right analysis pattern,
but its schema expects old fields such as:

```text
parent_feasibility_tier_id
normalized_surface_variant
sampled_obstacle_label
```

The M2125 artifact instead carries comparison-support metadata:

```text
candidate_id
candidate_set_id
scenario_redesign_branch
comparison_support_intent
target_support_tier
dynamics_band
obstacle_timing_band
road_width_band
initial_speed_band
materialization_semantics=comparison_support_smoke_proxy
```

Therefore M2128 should implement a comparison-support-specific localizer,
reusing the same no-rerun grouping and support-label semantics while changing
the required schema and aggregate slices.

## Frozen Command

M2128 must implement and run:

```bash
PYTHONPATH=src python -m autodrift.paper_route_outcome_supported_decisive_comparison_support_outcome_localization \
  --summary runs/m2125_paper_route_outcome_supported_decisive_comparison_support_measured_execution/summary.json \
  --episode-rows runs/m2125_paper_route_outcome_supported_decisive_comparison_support_measured_execution/episode_rows.csv \
  --output-dir runs/m2128_paper_route_outcome_supported_decisive_comparison_support_outcome_localization \
  --target-episode-count 1200 \
  --target-profile-count 5 \
  --target-spec-count 240 \
  --target-intent-count 4 \
  --target-support-tier-count 4 \
  --next-blocker m2129-paper-route-outcome-supported-decisive-comparison-support-outcome-localization-result-audit
```

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_paper_route_outcome_supported_decisive_comparison_support_outcome_localization.py
```

## Required Outputs

M2128 must write:

```text
summary.json
success_rows.csv
comparison_support_candidates.csv
comparison_ready_candidates.csv
offtrack_dominance_slices.csv
collision_dominance_slices.csv
claim_boundary.csv
outcome_by_profile.csv
outcome_by_intent.csv
outcome_by_target_support_tier.csv
outcome_by_source_kind.csv
outcome_by_proxy_template.csv
outcome_by_profile_intent.csv
outcome_by_profile_target_support_tier.csv
outcome_by_intent_source_kind.csv
outcome_by_source_profile.csv
outcome_by_task_intent_kind.csv
run_state.json
```

The localizer must reproduce M2125 source outcome counts exactly:

```text
success_obstacle_pass: 188
collision_failure: 144
off_track_noncollision_noncompletion: 868
```

## Comparison-Ready Criteria

The localizer labels an aggregate slice `comparison_ready_candidate` only if:

```text
episode_count >= 24
success_count >= 6
success_profile_count >= 3
success_source_count >= 3
collision_rate < 0.30
offtrack_outcome_rate < 0.70
```

It labels a weaker `candidate_support` slice only if:

```text
episode_count >= 12
success_count >= 3
success_profile_count >= 2
collision_rate < 0.40
offtrack_outcome_rate < 0.85
```

These labels are admission evidence for later audit only. M2128 must not rank
profiles even if comparison-ready candidates exist.

## Claim Boundary

Supported:

```text
M2127 defines a no-rerun localization route over the complete M2125 measured
artifact with explicit comparison-ready criteria.
```

Unsupported:

```text
localization has been run;
comparison-ready support exists;
controller-family ranking;
finite-window-vs-GRU conclusion;
paper-level benchmark evidence;
level3 self-identification.
```

## Next

Next milestone:

```text
m2128-paper-route-outcome-supported-decisive-comparison-support-outcome-localization-implementation
```
