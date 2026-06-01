# M2155 Paper-Route Current-Sim Controlled Comparison Reset Validation Result Audit

- status: completed
- decision: `current_sim_reset_validation_audit_route_to_terminal_boundary_sampling_diagnostic_design`
- audited summary: `runs/m2154_paper_route_current_sim_controlled_comparison_reset_validation_preflight/summary.json`
- reset rerun in M2155: `false`
- rollout/measured execution in M2155: `false`
- policy actions executed in M2155: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- failure taxonomy: `scenario_sampling_failure`

## Audit Result

M2154 is a fail-closed reset-validation result caused by one localized
terminal-boundary obstacle-sampling failure. It is not a schema, actor-input
contract, metadata, forbidden-key, quota, or guardrail failure.

```text
result_class: current_sim_controlled_comparison_reset_validation_preflight_fail
input_executable_spec_count: 40
target_executable_spec_count: 40
reset_attempt_count: 40
reset_success_count: 39
reset_failure_count: 1
observation_finite_count: 39
observation_dimension_failure_count: 0
obstacle_initialized_count: 39
contract_violation_count: 0
metadata_missing_count: 0
forbidden_key_violation_count: 0
task_family_quota_pass: true
source_family_template_quota_pass: true
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

Failing row:

```text
task_source_id: m2151-current-sim-t5-03
benchmark_spec_id: current_sim_benchmark_v0_t5
task_family: T5_terminal_boundary_near_constraint
claim_level_target: Claim_D_strong_self_identification
source_kind: terminal_boundary
source_family_template: t5_high_speed_close_obstacle
capability_pair: terminal_boundary
source_index: 3
source_seed: 215503
eval_seed_override: 219103
reset_eval_seed: 215335
reveal_step: 64
error_type: RuntimeError
error_message: failed to sample an obstacle scenario matching the configured filters
```

Static config inspection shows that the failing spec is a close/high-speed
terminal-boundary task:

```text
obstacle.distance_range: [10.0, 22.0]
obstacle.half_width_range: [0.75, 1.35]
obstacle.max_sample_attempts: 200
obstacle.allowed_labels: aeb_feasible, aes_feasible, drift_required, unavoidable
obstacle.require_aeb_infeasible: false
randomization.mu_range: [0.25, 0.95]
randomization.brake_scale_range: [0.45, 1.20]
randomization.actuator_tau_scale_range: [0.90, 2.80]
```

The allowed label set is broad, so the failure is most likely caused by the
combination of terminal-boundary geometry, hidden-dynamics randomization,
obstacle filtering, and the `200` attempt budget under the frozen reset seed.
M2155 does not rerun reset, so it cannot yet distinguish a seed-local miss from
a systematically brittle T5 template.

## Classification

Failure type:

```text
scenario_sampling_failure
```

Rationale:

- one and only one spec failed environment reset;
- the error is the simulator's obstacle-scenario sampling failure;
- contract, metadata, forbidden-key, task-family/source-family quota, and
  guardrail counts are all `0`;
- no policy action, rollout, training, replay, PPO, checkpoint update, ranking,
  or self-ID test ran.

This is not classified as:

```text
contract_violation:
  contract_violation_count == 0 and actor-input metadata is clean.

metric_artifact:
  the failing gate is a real reset failure, not a stale quota mismatch.

training_instability / proof_washout / behavior_regression:
  no policy update or rollout ran.
```

## Supported Claims

M2155 supports:

- M2154 executed only reset validation;
- `39/40` M2151 current-sim executable specs reset successfully;
- all successful reset observations are finite and 72-dimensional;
- the reset validator preserves the M2151 current-sim metadata and claim
  boundary;
- one T5 terminal-boundary row blocks reset-valid status;
- the next route should diagnose terminal-boundary sampling before repair or
  measured execution.

M2155 does not support:

- marking the M2151 current-sim panel reset-valid;
- dropping the failing row without a registered rule;
- rerunning with a different seed and treating it as the same gate;
- measured rollout success;
- controller-family ranking;
- finite-window vs GRU comparison;
- paper-level benchmark evidence;
- level3 self-identification.

## Next Route

Decision:

```text
route_to_terminal_boundary_reset_sampling_diagnostic_design
```

M2156 should design a bounded diagnostic over the single failing row before any
repair. The diagnostic should be reset-only and should compare:

```text
frozen reset seed: 215335
materialized eval_seed_override: 219103
attempt budgets: 200, 800, 1600
expected observation dimension: 72
target task_source_id: m2151-current-sim-t5-03
```

The diagnostic may run resets only in the later implementation milestone. It
must not execute policy actions, train, tune controller profiles, rank
controller families, or claim paper/self-ID evidence. If the failing row passes
with a larger attempt budget, the follow-up repair should parameterize the T5
reset-sampling attempt budget. If it still fails, the follow-up repair should
retarget the terminal-boundary geometry or replace the spec through a
pre-registered source-diverse rule.

Immediate next milestone:

```text
m2156-paper-route-current-sim-terminal-boundary-reset-sampling-diagnostic-design
```
