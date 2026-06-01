# M2159 Paper-Route Current-Sim Terminal-Boundary Reset-Sampling Diagnostic Result Audit

- status: completed
- decision: `terminal_boundary_diagnostic_audit_route_to_reset_validator_seed_source_repair_design`
- audited summary: `runs/m2158_paper_route_current_sim_terminal_boundary_reset_sampling_diagnostic/summary.json`
- reset rerun in M2159: `false`
- rollout/measured execution in M2159: `false`
- policy actions executed in M2159: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- failure taxonomy: `scenario_sampling_failure`, `metric_artifact`

## Audit Result

M2158 cleanly classifies the M2154 blocker as a seed-source protocol issue,
not as terminal-boundary attempt-budget brittleness.

```text
result_class: current_sim_terminal_boundary_reset_sampling_diagnostic_complete
target_task_source_id: m2151-current-sim-t5-03
target_spec_count: 1
diagnostic_attempt_count: 6
observed_eval_seed_count: 2
observed_attempt_budget_count: 3
reset_success_count: 3
reset_failure_count: 3
diagnostic_classification: seed_local_sampling_failure
contract_violation_count: 0
metadata_missing_count: 0
forbidden_key_violation_count: 0
guardrail_violation_count: 0
```

The attempt matrix is decisive:

```text
eval_seed=215335, attempt_budget=200:  fail
eval_seed=215335, attempt_budget=800:  fail
eval_seed=215335, attempt_budget=1600: fail
eval_seed=219103, attempt_budget=200:  pass
eval_seed=219103, attempt_budget=800:  pass
eval_seed=219103, attempt_budget=1600: pass
```

M2154 used:

```text
actual reset seed = eval_seed_base + row_index = 215335
```

The materialized M2151 spec already contains:

```text
eval_seed_override = 219103
```

That seed resets the same T5 spec successfully with the original
`max_sample_attempts=200`. Therefore increasing the attempt budget is not the
right first repair. The reset-validation protocol should respect per-spec
`eval_seed_override` when present, and only fall back to `eval_seed_base +
row_index` for specs without an override.

## Classification

Failure types:

```text
scenario_sampling_failure:
  M2154's sequential reset seed really failed to sample the obstacle scenario.

metric_artifact:
  M2154's reset-validation gate used a seed source inconsistent with the
  materialized executable spec's own eval_seed_override.
```

This is not classified as:

```text
terminal_boundary_template_brittle:
  the materialized seed passes at the original 200-attempt budget.

attempt_budget_limited:
  the original failing seed still fails at 800 and 1600 attempts.

contract_violation:
  contract_violation_count == 0.

training_instability / proof_washout / behavior_regression:
  no training, replay, PPO, rollout, or checkpoint update ran.
```

## Supported Claims

M2159 supports:

- M2158 ran the intended bounded diagnostic without rollout or policy action;
- the M2154 failure is seed-local under the tested seeds and budgets;
- `eval_seed_override=219103` is a valid reset seed for the failing spec;
- the next repair should target reset-validation seed selection, not controller
  behavior or T5 attempt-budget inflation.

M2159 does not support:

- full 40-spec reset validity;
- measured rollout success;
- controller-family ranking;
- finite-window vs GRU comparison;
- winner selection;
- paper-level benchmark evidence;
- level3 self-identification.

## Next Route

Decision:

```text
route_to_reset_validator_seed_source_repair_design
```

M2160 should design a reset-validator repair with these rules:

```text
if spec.eval_seed_override is present:
  use spec.eval_seed_override as the reset seed;
  record seed_source = eval_seed_override.
else:
  use eval_seed_base + row_index;
  record seed_source = eval_seed_base_plus_index.
```

The repaired reset validator should rerun the full 40-spec panel only after the
repair is designed and implemented. It should preserve current-sim metadata,
actor-input contract checks, no-rollout/no-policy-action guardrails, and the
claim boundary that reset validity is still not measured controller
performance.

Immediate next milestone:

```text
m2160-paper-route-current-sim-reset-validator-seed-source-repair-design
```
