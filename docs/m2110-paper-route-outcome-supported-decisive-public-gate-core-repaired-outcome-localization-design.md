# M2110 Paper-Route Outcome-Supported Decisive Public-Gate Core Repaired Outcome Localization Design

- status: completed
- decision: `public_gate_core_repaired_outcome_localization_design_route_to_no_rerun_implementation`
- reset/rollout/measured execution in M2110: `false`
- policy actions executed in M2110: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design

M2110 reuses the existing no-rerun localizer:

```text
src/autodrift/paper_route_controlled_routing_smoke_outcome_localization.py
```

It reads only M2108 artifacts and must not reset or roll out the environment.

Frozen M2111 command:

```bash
PYTHONPATH=src python -m autodrift.paper_route_controlled_routing_smoke_outcome_localization \
  --summary runs/m2108_paper_route_outcome_supported_decisive_public_gate_core_repaired_measured_execution/summary.json \
  --episode-rows runs/m2108_paper_route_outcome_supported_decisive_public_gate_core_repaired_measured_execution/episode_rows.csv \
  --output-dir runs/m2111_paper_route_outcome_supported_decisive_public_gate_core_repaired_outcome_localization \
  --target-episode-count 480 \
  --target-profile-count 5 \
  --target-spec-count 96 \
  --target-family-count 3 \
  --next-blocker m2112-paper-route-outcome-supported-decisive-public-gate-core-repaired-outcome-localization-result-audit
```

Focused test:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_paper_route_controlled_routing_smoke_outcome_localization.py
```

## Required Outputs

M2111 must write:

```text
summary.json
success_rows.csv
comparison_support_candidates.csv
offtrack_dominance_slices.csv
collision_dominance_slices.csv
claim_boundary.csv
outcome_by_profile.csv
outcome_by_family.csv
outcome_by_source_kind.csv
outcome_by_proxy_template.csv
outcome_by_generated_proxy.csv
outcome_by_sampled_label.csv
outcome_by_profile_family.csv
outcome_by_profile_source_kind.csv
outcome_by_profile_generated_proxy.csv
outcome_by_source_profile.csv
outcome_by_source_family_kind.csv
run_state.json
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

No controller ranking is allowed in M2111 even if candidates exist. M2112 must
audit candidates and decide the next route.

## Claim Boundary

Supported:

```text
M2110 defines a no-rerun localization route over the complete M2108 artifact
with explicit comparison-ready criteria.
```

Unsupported:

```text
localization has been run;
controller-family ranking;
paper-level benchmark evidence;
finite-window-vs-GRU conclusion;
level3 self-identification.
```

## Next

Next milestone:

```text
m2111-paper-route-outcome-supported-decisive-public-gate-core-repaired-outcome-localization-implementation
```
