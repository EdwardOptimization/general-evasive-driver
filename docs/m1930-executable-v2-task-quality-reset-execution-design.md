# M1930 Executable V2 Task-Quality Reset Execution Design

- status: completed
- decision: `task_quality_reset_execution_design_admit_reset_validator_implementation`
- branch: `paper_route_task_quality_reset_execution`
- parent synthesis: `docs/m1929-executable-v2-task-quality-scenario-redesign-branch-synthesis.md`
- input specs: `runs/m1928_executable_v2_task_quality_scenario_redesign_materialization_preflight/executable_task_specs.json`
- workload matrix: `runs/m1928_executable_v2_task_quality_scenario_redesign_materialization_preflight/executable_workload_matrix.csv`
- first execution stage: `reset_only_validation`
- reset/rollout/measured execution in M1930: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Decision

M1930 selects a staged reset-first route over the M1928 executable
task-quality panel.

The next executable step must be reset-only validation of the `80`
materialized task specs. It must not run a policy action, measured rollout,
controller-family comparison, training, replay, PPO, promotion, private
holdout evaluation, paper-level claim, or level3 self-ID claim.

This ordering is intentional:

```text
M1928 executable specs
  -> M1931 reset validator implementation, mocked/focused tests only
  -> M1932 reset-validation command design
  -> M1933 reset-only validation execution over 80 specs
  -> result audit
  -> only then consider 960-row measured rollout execution
```

The `960` workload rows from M1928 remain materialized future work. They are
not reset individually in the first stage because reset feasibility is a
scenario-spec property, not a controller-profile property. Controller profiles
become relevant only after scenario reset validation passes.

## Compatibility With Existing Reset Helpers

Existing reset helpers provide useful boundary rules but are not exact command
targets for M1928.

Reusable constraints:

```text
src/autodrift/executable_v2_reset_feasibility_preflight.py
  runs reset-only validation, preserves sampling failures, forbids policy
  action and measured rollout, writes reset rows and aggregate distributions.

src/autodrift/executable_v2_support_first_reset_validation_adapter.py
  shows the no-reset adapter pattern and guardrail flags for keeping reset
  payload construction separate from environment execution.
```

Why a focused M1931 helper is still required:

```text
M1793 reset preflight expects executable_v2_panel_specs and profile configs.
M1928 writes executable_task_specs with embedded env_config payloads.
M1928 profile_name in the workload matrix is controller-profile metadata, not
scenario reset metadata.
```

Forcing M1928 through the old helper would add an unnecessary schema
translation layer and increase the risk of silently mixing scenario metadata
with controller identity. M1931 should instead consume M1928
`executable_task_specs.json` directly.

## M1931 Implementation Target

M1931 should implement a focused helper, tentatively:

```text
src/autodrift/executable_v2_task_quality_reset_validation_preflight.py
tests/test_executable_v2_task_quality_reset_validation_preflight.py
```

The helper should:

- load `executable_task_specs` from the M1928 payload;
- sort rows deterministically by `task_source_id`;
- rebuild each environment with `build_env_config(spec["env_config"])`;
- instantiate `AutoDriftEnv`;
- call `env.reset(seed=eval_seed_base + index)`;
- close the environment in all success/failure paths;
- record reset successes and preserved exceptions;
- check observation finiteness and expected observation dimension;
- verify obstacle initialization through reset `info`;
- keep labels, tiers, and source roles as artifact metadata only;
- report the human-view contract fields from each embedded config.

It should not:

- load any checkpoint;
- load any controller-profile policy;
- execute any action;
- run a rollout step;
- run measured execution;
- train, replay, or run PPO;
- use private holdout rows;
- change actor inputs;
- compare or rank controller families.

## M1932/M1933 Planned Command

After M1931 implementation and tests pass, M1932 should register a command
equivalent to:

```bash
PYTHONPATH=src python -m autodrift.executable_v2_task_quality_reset_validation_preflight \
  --executable-task-specs runs/m1928_executable_v2_task_quality_scenario_redesign_materialization_preflight/executable_task_specs.json \
  --output-dir runs/m1933_executable_v2_task_quality_reset_validation_preflight \
  --eval-seed-base 193300 \
  --target-spec-count 80 \
  --next-blocker m1934-executable-v2-task-quality-reset-validation-result-audit
```

The exact command should be frozen in M1932 before M1933 runs it.

## Target Artifacts

M1933 reset-only validation should write:

```text
runs/m1933_executable_v2_task_quality_reset_validation_preflight/summary.json
runs/m1933_executable_v2_task_quality_reset_validation_preflight/reset_rows.csv
runs/m1933_executable_v2_task_quality_reset_validation_preflight/reset_failure_rows.csv
runs/m1933_executable_v2_task_quality_reset_validation_preflight/contract_rows.csv
runs/m1933_executable_v2_task_quality_reset_validation_preflight/reset_distribution_by_tier.csv
runs/m1933_executable_v2_task_quality_reset_validation_preflight/reset_distribution_by_role.csv
runs/m1933_executable_v2_task_quality_reset_validation_preflight/reset_distribution_by_surface.csv
runs/m1933_executable_v2_task_quality_reset_validation_preflight/claim_boundary.csv
```

## M1933 Reset Pass Gates

The first reset execution should pass only if:

```text
input_executable_spec_count == 80
reset_attempt_count == 80
reset_success_count == 80
reset_failure_count == 0
observation_finite_count == 80
observation_dimension_failure_count == 0
obstacle_initialized_count == 80
contract_violation_count == 0
label_actor_input_violation_count == 0
forbidden_key_violation_count == 0
guardrail_violation_count == 0
private_holdout_used == false
environment_reset_started == true
environment_rollout_started == false
policy_action_executed == false
measured_rollout_started == false
training_started == false
replay_started == false
ppo_used == false
controller_family_ranking_claim_made == false
paper_level_claim_made == false
level3_self_id_claim_made == false
```

If any reset fails, the run should fail closed, preserve the exception in
`reset_failure_rows.csv`, and route to a failure audit instead of repair or
rerun.

## Failure Taxonomy

M1933 failures should be classified before any repair:

```text
schema_incompatible:
  M1928 payload cannot be loaded or required fields are missing.

env_config_rebuild_failure:
  build_env_config rejects the embedded env_config.

human_view_contract_violation:
  privileged params, wheel observations, nonzero obstacle relative velocity,
  path/reference/TTC-like shortcuts, or label leakage are detected.

reset_sampling_failure:
  AutoDriftEnv.reset raises or cannot sample the fixed obstacle scenario.

observation_contract_failure:
  reset returns non-finite observation or unexpected observation dimension.

metadata_join_failure:
  tier, role, source, or surface metadata cannot be preserved in output rows.

guardrail_violation:
  any forbidden action, rollout, training, ranking, holdout, paper, or self-ID
  flag becomes true.
```

## Claim Boundary

If M1933 passes, it may claim only:

```text
the M1928 80-spec public task-quality scenario panel is reset-valid under the
current simulator and human-view observation contract.
```

It still cannot claim:

- any controller family is better;
- any controller policy succeeds on the panel;
- any RL driver improved;
- any finite-window/GRU/self-ID conclusion;
- any paper-level benchmark result;
- any high-fidelity or sim-to-real readiness.

Those claims require later measured rollout, multi-seed evaluation, baselines,
holdout discipline, and mechanism tests.

## Next

Next milestone:

```text
m1931-executable-v2-task-quality-reset-validator-implementation
```

M1931 should implement the focused reset validator and mocked/focused tests
without running the real M1928 reset workload.
