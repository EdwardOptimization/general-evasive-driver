# M2128 Paper-Route Outcome-Supported Decisive Comparison-Support Outcome Localization Implementation

- status: completed
- decision: `comparison_support_outcome_localization_pass_route_to_result_audit`
- run artifact: `runs/m2128_paper_route_outcome_supported_decisive_comparison_support_outcome_localization/summary.json`
- focused tests: `3 passed`
- reset/rollout/measured execution in M2128: `false`
- policy actions executed in M2128: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Implementation Summary

M2128 adds a comparison-support-specific no-rerun localizer:

```text
src/autodrift/paper_route_outcome_supported_decisive_comparison_support_outcome_localization.py
tests/test_paper_route_outcome_supported_decisive_comparison_support_outcome_localization.py
```

It reads only M2125 artifacts and does not reset or roll out the environment.
It adapts the old localization pattern to the M2125 schema:

```text
comparison_support_intent
target_support_tier
dynamics_band
obstacle_timing_band
road_width_band
initial_speed_band
```

## Command

Executed:

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

## Result

M2128 passes no-rerun localization:

```text
result_class: comparison_support_outcome_localization_pass
episode_count: 1200
profile_count: 5
spec_count: 240
intent_count: 4
support_tier_count: 4
outcome_counts_match_source_summary: true
missing_schema_fields: []
all_selected_metrics_finite: true
required_files_written: true
guardrail_violation_count: 0
```

Outcome counts reproduce M2125 exactly:

```text
success_obstacle_pass: 188
collision_failure: 144
off_track_noncollision_noncompletion: 868
```

Localization outputs:

```text
success_row_count: 188
comparison_ready_candidate_count: 15
comparison_support_candidate_count: 37
offtrack_dominance_slice_count: 92
collision_dominance_slice_count: 27
```

The comparison-ready candidates are admission evidence for audit, not a
controller-family ranking.

## Claim Boundary

Supported:

```text
The complete M2125 artifact has been localized without rerun, preserving exact
outcome counts and producing support/dominance diagnostic artifacts.
```

Unsupported:

```text
controller-family ranking;
finite-window-vs-GRU conclusion;
paper-level benchmark evidence;
level3 self-identification.
```

## Next

Next milestone:

```text
m2129-paper-route-outcome-supported-decisive-comparison-support-outcome-localization-result-audit
```
