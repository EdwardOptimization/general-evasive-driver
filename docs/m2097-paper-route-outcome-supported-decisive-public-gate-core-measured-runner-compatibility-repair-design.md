# M2097 Paper-Route Outcome-Supported Decisive Public-Gate Core Measured Runner Compatibility Repair Design

- status: completed
- decision: `public_gate_core_measured_runner_compatibility_repair_design_admit_no_rollout_implementation`
- parent design: `docs/m2096-paper-route-outcome-supported-decisive-public-gate-core-measured-execution-command-design.md`
- source specs: `runs/m2094_paper_route_outcome_supported_decisive_public_gate_core_panel_extraction/public_gate_core_executable_task_specs.json`
- source workload: `runs/m2094_paper_route_outcome_supported_decisive_public_gate_core_panel_extraction/public_gate_core_planned_sentinel_workload.csv`
- reset/rollout/measured execution in M2097: `false`
- policy actions executed in M2097: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Goal

M2096 localized the next blocker to measured-runner metadata compatibility:

```text
missing required spec field: panel_source_id
missing required workload fields: proxy_template_family, generated_source_row
```

M2097 freezes a no-rollout metadata enrichment step. The repair must not change
scenario semantics, env configs, obstacle filters, controller profiles, or
measured runner validation.

## Exact Mapping

For each executable spec:

```text
panel_source_id := source_reference
```

`source_reference` is non-empty and unique over the 96 public-gate core specs.
It is the closest existing candidate/source identifier in the M2094 schema.

For each workload row, join the source spec by `task_source_id` and set:

```text
proxy_template_family := spec.proxy_template_family
generated_source_row := spec.generated_source_row
```

The repair must preserve all existing workload rows and keys:

```text
workload_id
task_source_id
profile_name
profile_config_path
checkpoint_path
```

The repair must preserve each spec's `env_config` exactly.

## M2098 Implementation Route

M2098 should add a no-rollout adapter:

```text
src/autodrift/paper_route_outcome_supported_decisive_public_gate_core_measured_runner_compatibility_repair.py
tests/test_paper_route_outcome_supported_decisive_public_gate_core_measured_runner_compatibility_repair.py
```

M2098 should run:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_outcome_supported_decisive_public_gate_core_measured_runner_compatibility_repair.py
```

Then:

```bash
PYTHONPATH=src python -m autodrift.paper_route_outcome_supported_decisive_public_gate_core_measured_runner_compatibility_repair \
  --public-gate-core-executable-task-specs runs/m2094_paper_route_outcome_supported_decisive_public_gate_core_panel_extraction/public_gate_core_executable_task_specs.json \
  --public-gate-core-workload runs/m2094_paper_route_outcome_supported_decisive_public_gate_core_panel_extraction/public_gate_core_planned_sentinel_workload.csv \
  --output-dir runs/m2098_paper_route_outcome_supported_decisive_public_gate_core_measured_runner_compatibility_repair \
  --target-spec-count 96 \
  --target-workload-count 480 \
  --target-profile-count 5 \
  --next-blocker m2099-paper-route-outcome-supported-decisive-public-gate-core-measured-runner-compatibility-repair-result-audit
```

## Required Artifacts

M2098 must write:

```text
public_gate_core_measured_compatible_executable_task_specs.json
public_gate_core_measured_compatible_executable_task_specs.csv
public_gate_core_measured_compatible_workload.csv
compatibility_validation_failure_rows.csv
env_config_integrity_rows.csv
claim_boundary.csv
summary.json
```

## Pass Gates

M2098 passes only if:

```text
compatible_spec_count == 96
compatible_workload_count == 480
profile_count == 5
spec_panel_source_id_missing_count == 0
workload_proxy_template_family_missing_count == 0
workload_generated_source_row_missing_count == 0
measured_runner_validation_failure_count == 0
env_config_changed_count == 0
duplicate_workload_id_count == 0
guardrail_violation_count == 0
environment_reset_started == false
environment_rollout_started == false
policy_action_executed == false
measured_rollout_started == false
training_started == false
replay_started == false
ppo_used == false
promoted == false
private_holdout_used == false
actor_input_contract_changed == false
profile_specific_tuning == false
controller_family_ranking_claim_made == false
finite_window_vs_gru_conclusion_made == false
paper_level_claim_made == false
level3_self_id_claim_made == false
```

## Claim Boundary

M2097/M2098 may claim only:

```text
measured-runner metadata compatibility was repaired without changing task
semantics or env configs.
```

They cannot claim:

```text
measured execution readiness before audit;
controller-family ranking;
paper-level benchmark evidence;
finite-window-vs-GRU conclusion;
level3 self-identification.
```

## Next

Next milestone:

```text
m2098-paper-route-outcome-supported-decisive-public-gate-core-measured-runner-compatibility-repair-implementation
```
