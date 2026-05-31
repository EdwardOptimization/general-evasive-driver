# M2030 Paper-Route T2/T3 Source Generation Preflight Result Audit

- status: completed
- decision: `t2_t3_source_generation_preflight_audit_admit_routing_smoke_command_design`
- audited summary: `runs/m2029_paper_route_t2_t3_source_generation_preflight/summary.json`
- audited coverage: `runs/m2029_paper_route_t2_t3_source_generation_preflight/source_coverage_projection.csv`
- audited claim boundary: `runs/m2029_paper_route_t2_t3_source_generation_preflight/claim_boundary.csv`
- reset/rollout/measured execution in M2030: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Result Audit

M2029 is a clean artifact-layer pass:

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

Projection:

```text
T1: 18 sources, 4 source kinds, max share 0.3333, pass
T2: 72 sources, 10 source kinds, max share 0.2917, pass
T3: 42 sources, 10 source kinds, max share 0.2143, pass
T4: 33 sources, 4 source kinds, max share 0.2727, pass
T5: 72 sources, 8 source kinds, max share 0.2917, pass
```

Claim boundary:

```text
panel_projected_ready_for_routing_smoke: true
controller_family_ranking: false
finite_window_vs_gru_conclusion: false
paper_level_benchmark_result: false
level3_self_identification: false
```

## T1 Target-Count Caveat

M2029's projected readiness uses the registered routing-smoke gates for this
branch:

```text
source_count >= 12
max_single_source_kind_share <= 0.35
```

T1 passes those gates:

```text
source_count = 18
max_single_source_kind_share = 0.3333
```

T1 does not pass the nonblocking target count:

```text
target_clean_sources_target = 24
target_clean_sources_pass = false
```

Audit decision:

```text
T1 target count does not block routing-smoke command design.
```

Rationale:

- Routing smoke should test plumbing, profile loading, workload schema,
  metric completeness, and guardrails.
- Paper-level benchmark execution remains blocked and can later require target
  count, holdout, or source-rich expansion.
- M2031 must label the next command as routing smoke only, not benchmark or
  ranking evidence.

## Supported Claims

Supported:

```text
M2029 generated clean no-rollout T2/T3 source rows.
The merged panel projection passes routing-smoke count/share gates for all
five families.
T2/T3 source-kind dominance is repaired at the artifact projection layer.
Routing-smoke command design is now admissible.
```

Unsupported:

```text
The generated sources are reset-valid.
The generated sources are rollout-valid.
The 12-profile controller matrix has been executed.
Controller families can be ranked.
Finite-window-vs-GRU can be concluded.
Paper-level benchmark evidence exists.
Level3 self-identification evidence exists.
```

## Failure Taxonomy

Failure type:

```text
none
```

Residual risks:

```text
generated_source_semantics:
  M2029 rows are deterministic source specs, not validated simulator states.

routing_smoke_scope:
  A smoke run can validate plumbing and schema, but not paper-level ranking.

t1_target_count:
  acceptable for smoke, but must be revisited before full benchmark claims.
```

## Route Decision

Decision:

```text
route_to_controlled_routing_smoke_command_design
```

Rejected routes:

```text
generated-source semantics repair:
  rejected for now because generated rows have clean claim flags and source
  projection passes with slack.

threshold/source-kind semantics audit:
  rejected for now because no threshold weakening is needed for smoke.

direct execution:
  rejected because the project requires command design before execution.

paper benchmark execution:
  rejected because no routing smoke has run and target/holdout requirements are
  not yet satisfied.
```

M2031 should design a bounded routing-smoke command over the M2029 merged panel.
It must keep the result scoped to plumbing/schema/guardrail validation and must
not claim ranking, finite-window-vs-GRU, paper-level evidence, or level3
self-identification.
