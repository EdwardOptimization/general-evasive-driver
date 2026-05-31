# M2029 Paper-Route T2/T3 Source Generation Preflight Implementation

- status: completed
- decision: `t2_t3_source_generation_preflight_pass_route_to_result_audit`
- result class: `t2_t3_source_generation_preflight_pass`
- manifest: `experiments/manifests/m2029-paper-route-t2-t3-source-generation-preflight-implementation.json`
- implementation: `src/autodrift/paper_route_t2_t3_source_generation_preflight.py`
- focused tests: `1 passed`
- compileall: `passed`
- summary: `runs/m2029_paper_route_t2_t3_source_generation_preflight/summary.json`
- reset/rollout/measured execution in M2029: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Result

M2029 implemented and ran the no-rollout T2/T3 source-generation preflight over
M2026 repaired panel sources.

```text
result_class: t2_t3_source_generation_preflight_pass
base_source_count: 183
generated_source_count: 54
generated_t2_source_count: 36
generated_t3_source_count: 18
merged_source_count: 237
expected_counts_met: true
duplicate_generated_source_ids: []
guardrail_violation_count: 0
panel_projected_ready_for_routing_smoke: true
```

No environment reset, rollout, policy action, measured execution, replay, PPO,
training, private holdout, profile tuning, actor-input change, threshold
weakening, T4/T5 relabeling, ranking claim, paper-level claim, or level3
self-ID claim occurred.

## Projection

Projected source coverage:

```text
T1_reactive_active_safety:
  source_count = 18
  source_kind_count = 4
  max_single_source_kind_share = 0.3333
  source_kind_share_pass = true

T2_same_current_different_older_history:
  source_count = 72
  source_kind_count = 10
  max_single_source_kind_share = 0.2917
  source_kind_share_pass = true

T3_active_diagnostic_warmup:
  source_count = 42
  source_kind_count = 10
  max_single_source_kind_share = 0.2143
  source_kind_share_pass = true

T4_variable_diagnostic_delay:
  source_count = 33
  source_kind_count = 4
  max_single_source_kind_share = 0.2727
  source_kind_share_pass = true

T5_source_rich_extreme_dynamics:
  source_count = 72
  source_kind_count = 8
  max_single_source_kind_share = 0.2917
  source_kind_share_pass = true
```

Before/after status:

```text
T1: already_ready
T2: passes_after_generation
T3: passes_after_generation
T4: already_ready
T5: already_ready
```

Note: T1 remains below the nonblocking target count of 24 (`18/24`) but passes
the registered routing-smoke readiness gates used in this branch:

```text
source_count >= 12
max_single_source_kind_share <= 0.35
```

M2030 should explicitly audit whether this is sufficient for routing smoke
before admitting execution.

## Generated Rows

Generated rows:

```text
T2 rows: 36
T3 rows: 18
```

T2 source kinds:

```text
same_current_brake_authority_older_history_proxy
same_current_yaw_authority_older_history_proxy
same_current_steer_lag_older_history_proxy
same_current_drive_brake_asymmetry_older_history_proxy
same_current_rear_lateral_authority_older_history_proxy
same_current_mixed_authority_older_history_proxy
```

T3 source kinds:

```text
warmup_brake_authority_proxy
warmup_yaw_authority_proxy
warmup_steer_lag_proxy
warmup_rear_lateral_authority_proxy
warmup_mixed_authority_proxy
warmup_terminal_boundary_recovery_proxy
```

All generated rows have clean claim-boundary flags:

```text
labels_enter_actor_input = false
profile_specific_tuning = false
controller_family_ranking_claim_made = false
paper_level_claim_made = false
level3_self_id_claim_made = false
```

## Supported Claims

Supported:

```text
M2029 generated no-rollout T2/T3 source specs and panel source rows.
The merged panel projection passes source count and source-kind share gates for
all five task families.
The T2/T3 source-kind dominance blockers from M2026/M2027 are repaired at the
artifact projection layer with slack.
```

Unsupported:

```text
The generated scenarios have been reset-validated.
The generated scenarios have been rolled out.
The controller matrix can be ranked.
Finite-window-vs-GRU can be concluded.
Paper-level benchmark evidence exists.
Level3 self-identification evidence exists.
```

## Route Decision

Decision:

```text
route_to_source_generation_preflight_result_audit
```

Rationale:

- M2029 is a positive artifact-layer result, but no execution has occurred.
- M2030 must audit the generated row semantics, coverage projection, T1 target
  count caveat, and claim boundary before any routing-smoke command design.
- If M2030 accepts the projection as routing-smoke-ready, the next branch can
  design a bounded routing smoke over the merged panel.

## Artifacts

```text
runs/m2029_paper_route_t2_t3_source_generation_preflight/summary.json
runs/m2029_paper_route_t2_t3_source_generation_preflight/generated_source_specs.csv
runs/m2029_paper_route_t2_t3_source_generation_preflight/generated_panel_sources.csv
runs/m2029_paper_route_t2_t3_source_generation_preflight/merged_panel_sources.csv
runs/m2029_paper_route_t2_t3_source_generation_preflight/source_coverage_projection.csv
runs/m2029_paper_route_t2_t3_source_generation_preflight/source_coverage_comparison.csv
runs/m2029_paper_route_t2_t3_source_generation_preflight/generation_actions.csv
runs/m2029_paper_route_t2_t3_source_generation_preflight/claim_boundary.csv
```

## M2030 Requirements

M2030 should audit M2029 without rerun or execution. It must decide whether to
route to:

```text
routing-smoke command design;
generated-source semantics repair;
threshold/source-kind semantics audit;
branch synthesis;
stop current route.
```

M2030 must not run environment rollout, train, replay, rank controller
families, or claim finite-window-vs-GRU/self-ID evidence.
