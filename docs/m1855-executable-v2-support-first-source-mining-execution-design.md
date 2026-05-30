# M1855 Executable V2 Support-First Source Mining Execution Design

- status: completed
- decision: `support_first_source_mining_execution_design_admit_run`
- branch: `paper_route_executable_v2_support_first_source_mining`
- parent template: `configs/executable_v2_support_first_candidate_templates_v0.json`
- source mining run: `false`
- materialized executable-v2 rows generated: `false`
- environment reset run: `false`
- rollout/training/replay/PPO: `false`

## Purpose

M1854 generated the V0 candidate template. M1855 fixes the exact no-reset source
mining command and expected audit boundaries before the run.

This milestone does not run the command.

## Exact M1856 Command

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

## Expected Inputs

The execution must use:

```text
template_id: support_first_candidate_templates_v0
candidate_row_count: 288
role_count: 4
speed_count: 6
mu_count: 6
surface_variant_count: 2
grid_cell_count_total: 465264
```

Expected roles:

```text
stable_aeb
stable_aes_only
drift_required_recovery
unavoidable_mitigation
```

## Expected Outputs

M1856 should write:

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

## Audit Boundaries

M1856 is allowed to claim:

- no-reset source mining executed over the fixed V0 template;
- role-specific supported/unsupported source counts;
- materialization-admissibility input was produced.

M1856 is not allowed to claim:

- reset feasibility;
- measured execution;
- controller-family ranking;
- source repair success;
- executable-v2 materialization;
- paper-level result;
- level3 self-identification.

M1857 must audit support by role before any materialization design. If a role
has zero supported sources, record that as a source-support result and do not
tune the V0 template as if it were the same experiment.

## Guardrails

- source mining run: `false`
- project artifact scan: `false`
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

- exact M1856 source mining command;
- expected input counts and output directory;
- M1856 execution route.

Unsupported:

- source mining result;
- materialized executable-v2 rows;
- reset feasibility;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
