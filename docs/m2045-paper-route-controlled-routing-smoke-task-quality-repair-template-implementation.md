# M2045 Paper-Route Controlled Routing Smoke Task-Quality Repair Template Implementation

- status: completed
- decision: `controlled_routing_smoke_task_quality_repair_templates_pass_route_to_audit`
- result class: `controlled_routing_smoke_task_quality_repair_templates_pass`
- implementation: `src/autodrift/paper_route_controlled_routing_smoke_task_quality_repair_templates.py`
- focused tests: `3 passed`
- artifact: `configs/paper_route_controlled_routing_smoke_task_quality_repair_candidates_v0.json`
- reset/rollout/measured execution in M2045: `false`
- policy actions executed in M2045: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Commands

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_paper_route_controlled_routing_smoke_task_quality_repair_templates.py
```

Result:

```text
3 passed
```

Template generation:

```bash
PYTHONPATH=src python -m autodrift.paper_route_controlled_routing_smoke_task_quality_repair_templates \
  --localization-summary runs/m2042_paper_route_controlled_routing_smoke_outcome_localization/summary.json \
  --output configs/paper_route_controlled_routing_smoke_task_quality_repair_candidates_v0.json \
  --next-blocker m2046-paper-route-controlled-routing-smoke-task-quality-repair-template-result-audit
```

Result:

```text
result_class=controlled_routing_smoke_task_quality_repair_templates_pass
candidate_source_count=192
quota_pass=True
guardrail_violation_count=0
```

## Artifact Gates

The artifact satisfies the M2044 design:

```text
candidate_source_count: 192
repair_axis_counts:
  l2_offtrack_relief: 64
  family_offtrack_relief: 48
  zero_success_source_kind_relief: 40
  success_neighborhood_expansion: 24
  generated_proxy_support_check: 16
source_split_counts:
  public_debug: 112
  public_gate: 80
quota_pass: true
generated_proxy_paper_claim_count: 0
guardrail_violation_count: 0
profile_specific_tuning_count: 0
```

Forbidden claims remain false:

```text
labels_enter_actor_input: 0
profile_specific_tuning: 0
controller_family_ranking_claim_made: 0
finite_window_vs_gru_conclusion_made: 0
paper_level_claim_made: 0
level3_self_id_claim_made: 0
```

## What Changed

M2045 adds a deterministic no-rollout template generator. It reads the M2042
localization artifacts and writes repair candidates for:

```text
L2 offtrack relief;
family-wide offtrack relief;
zero-success source-kind relief;
success-neighborhood expansion;
generated-proxy support checking.
```

Each candidate carries parent evidence, repair axis, split, template delta
fields, and explicit no-claim guardrails. Generated proxy candidates remain:

```text
target_materialization_semantics=smoke_proxy
target_paper_validity_claim=false
```

## Supported Claims

Supported:

```text
a deterministic repair-template artifact exists;
the artifact matches the registered quotas;
the artifact is no-rollout and guardrail-clean;
it is ready for result audit before source mining or materialization.
```

Unsupported:

```text
reset validity;
rollout validity;
measured execution success;
controller-family ranking;
finite-window-vs-GRU conclusion;
paper-level benchmark result;
level3 self-identification.
```

## Next

M2046 should audit the template artifact before any source mining,
materialization, reset validation, measured execution, or ranking.
