# M2161 Paper-Route Current-Sim Reset-Validator Seed-Source Repair Implementation and Run

- status: completed
- decision: `seed_source_repaired_reset_validation_preflight_pass_route_to_result_audit`
- parent design: `docs/m2160-paper-route-current-sim-reset-validator-seed-source-repair-design.md`
- implementation: `src/autodrift/paper_route_current_sim_controlled_comparison_reset_validation_preflight.py`
- tests: `tests/test_paper_route_current_sim_controlled_comparison_reset_validation_preflight.py`
- summary: `runs/m2161_paper_route_current_sim_seed_source_repaired_reset_validation_preflight/summary.json`
- environment reset started: `true`
- environment rollout started: `false`
- policy action executed: `false`
- measured execution started: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Implementation

M2161 updates the reset-only validator so seed selection is explicit and
auditable. The default behavior remains the old sequential seed rule, but the
new manifest-controlled mode uses materialized per-spec seeds:

```text
--seed-source-mode prefer_spec_eval_seed_override
```

In that mode, each reset row records:

```text
row_index
eval_seed_base
eval_seed
actual_eval_seed
seed_source
seed_source_parse_error
```

The M2161 run also writes:

```text
reset_distribution_by_seed_source.csv
```

## Command

M2161 ran the frozen seed-source repaired reset-validation command:

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

```text
tests/test_paper_route_current_sim_controlled_comparison_reset_validation_preflight.py: 4 passed
```

## Result

M2161 passes the repaired reset-only gate.

```text
result_class: current_sim_controlled_comparison_reset_validation_preflight_pass
seed_source_mode: prefer_spec_eval_seed_override
input_executable_spec_count: 40
target_executable_spec_count: 40
reset_attempt_count: 40
reset_success_count: 40
reset_failure_count: 0
observation_dimension_failure_count: 0
observation_finite_count: 40
obstacle_initialized_count: 40
contract_violation_count: 0
metadata_missing_count: 0
forbidden_key_violation_count: 0
task_family_quota_pass: true
source_family_template_quota_pass: true
seed_source_quota_pass: true
seed_source_parse_failure_count: 0
guardrail_violation_count: 0
environment_reset_started: true
environment_rollout_started: false
policy_action_executed: false
measured_rollout_started: false
training_started: false
replay_started: false
ppo_used: false
controller_family_ranking_claim_made: false
winner_selected: false
finite_window_vs_gru_conclusion_made: false
paper_level_claim_made: false
level3_self_id_claim_made: false
```

Seed-source distribution:

```text
eval_seed_override: 40
```

This repairs the M2154 reset-validation failure as a seed-source protocol
artifact. The previously failing terminal-boundary row is no longer evaluated
with the accidental sequential seed; it uses the seed materialized into the
executable spec.

## Artifacts

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

## Supported Claims

M2161 supports:

- the M2151 current-sim executable-spec panel resets successfully under its
  materialized per-spec eval seeds;
- the reset validator now records seed provenance for each reset row;
- the repaired 40-spec reset gate has clean metadata, contract,
  forbidden-key, quota, and guardrail counts.

M2161 does not support:

- measured execution;
- policy behavior or controller-family ranking;
- winner selection;
- paper-level benchmark evidence;
- finite-window vs GRU comparison;
- level3 self-identification.

## Next

Next milestone:

```text
m2162-paper-route-current-sim-seed-source-repaired-reset-validation-result-audit
```

M2162 must audit the repaired reset-validation pass before any measured
execution command design or controller comparison.
