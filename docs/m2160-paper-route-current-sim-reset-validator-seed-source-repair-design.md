# M2160 Paper-Route Current-Sim Reset-Validator Seed-Source Repair Design

- status: completed
- decision: `reset_validator_seed_source_repair_design_admit_implementation_and_run`
- parent audit: `docs/m2159-paper-route-current-sim-terminal-boundary-reset-sampling-diagnostic-result-audit.md`
- reset rerun in M2160: `false`
- rollout/measured execution in M2160: `false`
- policy actions executed in M2160: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Repair Rule

M2159 shows that the current reset validator used a sequential seed that is not
the seed materialized into the executable spec. The repaired validator should
therefore choose reset seeds as:

```text
if spec.eval_seed_override is present and parseable:
  actual_eval_seed = spec.eval_seed_override
  seed_source = eval_seed_override
else:
  actual_eval_seed = eval_seed_base + row_index
  seed_source = eval_seed_base_plus_index
```

The repair must log both `seed_source` and `actual_eval_seed` in reset rows.
It must preserve the current-sim metadata, human-view actor-input contract,
no-rollout/no-policy-action guardrails, and claim boundaries.

This is not a controller-profile change, not an actor-input change, and not a
scenario retuning step. It is a reset-validation protocol repair so that the
validator uses the deterministic seed already produced by M2151 materialization.

## Frozen Command

M2161 must implement the repair and run exactly:

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_controlled_comparison_reset_validation_preflight \
  --executable-task-specs runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/executable_task_specs.json \
  --output-dir runs/m2161_paper_route_current_sim_seed_source_repaired_reset_validation_preflight \
  --eval-seed-base 215300 \
  --target-spec-count 40 \
  --expected-observation-dim 72 \
  --seed-source-mode prefer_spec_eval_seed_override \
  --next-blocker m2162-paper-route-current-sim-seed-source-repaired-reset-validation-result-audit
```

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_paper_route_current_sim_controlled_comparison_reset_validation_preflight.py
```

## Planned Artifacts

M2161 must write:

```text
runs/m2161_paper_route_current_sim_seed_source_repaired_reset_validation_preflight/summary.json
runs/m2161_paper_route_current_sim_seed_source_repaired_reset_validation_preflight/reset_rows.csv
runs/m2161_paper_route_current_sim_seed_source_repaired_reset_validation_preflight/reset_failure_rows.csv
runs/m2161_paper_route_current_sim_seed_source_repaired_reset_validation_preflight/contract_rows.csv
runs/m2161_paper_route_current_sim_seed_source_repaired_reset_validation_preflight/reset_distribution_by_task_family.csv
runs/m2161_paper_route_current_sim_seed_source_repaired_reset_validation_preflight/reset_distribution_by_source_family_template.csv
runs/m2161_paper_route_current_sim_seed_source_repaired_reset_validation_preflight/reset_distribution_by_seed_source.csv
runs/m2161_paper_route_current_sim_seed_source_repaired_reset_validation_preflight/metadata_missing_rows.csv
runs/m2161_paper_route_current_sim_seed_source_repaired_reset_validation_preflight/claim_boundary.csv
runs/m2161_paper_route_current_sim_seed_source_repaired_reset_validation_preflight/run_state.json
```

## Pass Gates

M2161 passes only if:

```text
result_class == current_sim_controlled_comparison_reset_validation_preflight_pass
seed_source_mode == prefer_spec_eval_seed_override
input_executable_spec_count == 40
target_executable_spec_count == 40
reset_attempt_count == 40
reset_success_count == 40
reset_failure_count == 0
observation_dimension_failure_count == 0
observation_finite_count == 40
obstacle_initialized_count == 40
contract_violation_count == 0
metadata_missing_count == 0
forbidden_key_violation_count == 0
task_family_quota_pass == true
source_family_template_quota_pass == true
seed_source_quota_pass == true
guardrail_violation_count == 0
environment_rollout_started == false
policy_action_executed == false
measured_rollout_started == false
controller_family_ranking_claim_made == false
paper_level_claim_made == false
level3_self_id_claim_made == false
```

The expected seed-source distribution for the M2151 panel is:

```text
eval_seed_override: 40
```

If any spec lacks `eval_seed_override`, M2161 may still run using fallback
seeds, but the summary must expose that via `seed_source_counts` and the result
must be audited before any measured execution.

## Claim Boundary

Supported after a clean M2161 run and M2162 audit:

```text
the current-sim executable-spec panel is reset-valid under its materialized
per-spec eval seeds.
```

Unsupported:

```text
measured execution;
policy behavior;
controller-family ranking;
winner selection;
paper-level benchmark evidence;
finite-window-vs-GRU conclusion;
level3 self-identification.
```

## Next

Next milestone:

```text
m2161-paper-route-current-sim-reset-validator-seed-source-repair-implementation-and-run
```
