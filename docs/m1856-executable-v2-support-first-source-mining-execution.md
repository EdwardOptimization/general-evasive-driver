# M1856 Executable V2 Support-First Source Mining Execution

- status: completed
- decision: `support_first_source_mining_execution_pass_route_to_result_audit`
- branch: `paper_route_executable_v2_support_first_source_mining`
- command source: `docs/m1855-executable-v2-support-first-source-mining-execution-design.md`
- result artifact: `runs/m1856_executable_v2_support_first_source_mining/summary.json`
- materialized executable-v2 rows generated: `false`
- environment reset run: `false`
- rollout/training/replay/PPO: `false`

## Execution

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.executable_v2_support_first_source_mining \
  --candidate-rows configs/executable_v2_support_first_candidate_templates_v0.json \
  --output-dir runs/m1856_executable_v2_support_first_source_mining \
  --support-evidence-artifact configs/executable_v2_support_first_candidate_templates_v0.json \
  --support-evidence-stage pre_materialization_source_mining \
  --claim-boundary-context project_artifact_execution \
  --next-blocker m1857-executable-v2-support-first-source-mining-result-audit
```

Result:

```text
candidate_source_count=288
supported_source_count=202
materialized_row_count=0
guardrail_violation_count=0
```

## Metric Hygiene Repair Before Final Result

The first M1856 run exposed two helper metric issues before this result was
recorded:

- insufficient accepted cells could leave a blank source failure reason;
- diversity used coarse speed/mu buckets and undercounted the fixed V0 values.

The helper was corrected before the final M1856 artifact was rerun:

```text
src/autodrift/executable_v2_support_first_source_mining.py
tests/test_executable_v2_support_first_source_mining.py
```

Focused repair tests:

```text
9 passed in 0.12s
```

Full tests after repair:

```text
1770 passed, 4 warnings in 10.45s
```

Final artifact check:

```text
blank unsupported failure reasons: 0
insufficient_accepted_cells failures: 9
speed_bucket_count: 6
mu_bucket_count: 6
```

## Role Results

```text
stable_aeb: 62 / 72 supported, accepted_cell_count_total=94675
stable_aes_only: 49 / 72 supported, accepted_cell_count_total=20996
drift_required_recovery: 49 / 72 supported, accepted_cell_count_total=10340
unavoidable_mitigation: 42 / 72 supported, accepted_cell_count_total=23748
```

Aggregate:

```text
candidate_source_count: 288
candidate_profile_count: 288
role_count: 4
supported_source_count: 202
unsupported_source_count: 86
blocked_candidate_count: 86
accepted_cell_count_total: 149759
labels_enter_actor_input_count: 0
materialized_row_count: 0
guardrail_violation_count: 0
```

Diversity:

```text
source_family_count: 2
profile_group_count: 4
role_count: 4
speed_bucket_count: 6
mu_bucket_count: 6
max_source_family_share: 0.5
max_profile_group_share: 0.25
```

## Generated Outputs

```text
runs/m1856_executable_v2_support_first_source_mining/summary.json
runs/m1856_executable_v2_support_first_source_mining/support_first_source_candidates.csv
runs/m1856_executable_v2_support_first_source_mining/support_first_profile_support.csv
runs/m1856_executable_v2_support_first_source_mining/support_first_accepted_cells.csv
runs/m1856_executable_v2_support_first_source_mining/support_first_blocked_candidates.csv
runs/m1856_executable_v2_support_first_source_mining/support_first_role_summary.csv
runs/m1856_executable_v2_support_first_source_mining/support_first_materialization_admissibility_input.csv
runs/m1856_executable_v2_support_first_source_mining/support_first_claim_boundary.csv
```

## Guardrails

- project artifact source mining run: `true`
- project artifact scan: `true`
- materialized executable-v2 rows generated: `false`
- source repair payload generated: `false`
- environment reset started: `false`
- environment rollout started: `false`
- policy action executed: `false`
- measured rollout started: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- reward changed: `false`
- dynamics changed: `false`
- termination behavior changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Claim Boundary

Supported:

- no-reset source mining executed over fixed V0 candidate template;
- role-separated support counts are available;
- materialization-admissibility input exists;
- result audit route.

Unsupported:

- materialized executable-v2 rows;
- reset feasibility;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
