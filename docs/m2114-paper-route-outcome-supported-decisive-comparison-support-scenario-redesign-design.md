# M2114 Paper-Route Outcome-Supported Decisive Comparison-Support Scenario Redesign Design

- status: completed
- decision: `comparison_support_scenario_redesign_design_route_to_candidate_generation`
- reset/rollout/measured execution in M2114: `false`
- policy actions executed in M2114: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Principle

M2113 closed the fixed public-gate smoke panel as comparison evidence. M2114
starts a new branch with a different objective:

```text
first make comparison support measurable,
then consider comparison;
do not rank aggregate profile rows before support gates pass.
```

This is not another repair of M2108/M2111. The next artifacts must be a new
scenario set designed to produce bounded slices where multiple profiles can
successfully complete enough tasks for a fair diagnostic comparison.

## Scenario Axes

M2115 should generate a no-rollout candidate set with four intent groups:

```text
support_ladder_easy: scenarios expected to produce multi-profile successes
support_ladder_medium: scenarios near the comparison boundary but not collision-only
discriminative_boundary: scenarios expected to separate current-response/window/GRU profiles
collision_relief_probe: scenarios derived from M2111 collision dominance but relaxed enough to admit support
```

Target candidate count:

```text
240 candidates total
60 support_ladder_easy
60 support_ladder_medium
60 discriminative_boundary
60 collision_relief_probe
```

The candidate generator must keep these fields explicit:

```text
candidate_id
scenario_redesign_branch
comparison_support_intent
target_support_tier
source_family
difficulty_axis
dynamics_band
obstacle_timing_band
road_width_band
paper_validity_claim=false
generated_source_row=true
profile_specific_tuning=false
```

## Support Gates

The branch cannot admit controller comparison until a measured artifact and
localization pass these support gates:

```text
comparison_ready_candidate_count >= 3
comparison_support_candidate_count >= 6
success_row_count >= 80
at least 3 profiles have successes in at least one comparison-ready slice
at least 3 source IDs contribute successes in each comparison-ready slice
collision_rate < 0.30 in comparison-ready slices
offtrack_outcome_rate < 0.70 in comparison-ready slices
```

If these gates fail, the route must synthesize or redesign the scenario
distribution. It must not compare profiles from unsupported aggregate rows.

## Claim Boundary

Supported:

```text
M2114 defines a new scenario-redesign branch with explicit support goals and
candidate generation targets.
```

Unsupported:

```text
candidate generation has been implemented;
scenarios are reset-valid;
measured support exists;
controller-family ranking;
paper-level benchmark evidence;
finite-window-vs-GRU conclusion;
level3 self-identification.
```

## Next

Next milestone:

```text
m2115-paper-route-outcome-supported-decisive-comparison-support-candidate-generation-implementation
```
