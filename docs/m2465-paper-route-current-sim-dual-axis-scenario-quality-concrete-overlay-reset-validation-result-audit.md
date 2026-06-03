# M2465 Paper-Route Current-Sim Dual-Axis Scenario-Quality Concrete Overlay Reset Validation Result Audit

- status: completed
- decision: `accept_reset_sampling_failure_route_to_r1_reset_sampling_diagnostic_panel`
- manifest: `experiments/manifests/m2465-paper-route-current-sim-dual-axis-scenario-quality-concrete-overlay-reset-validation-result-audit.json`
- parent implementation: `docs/m2464-paper-route-current-sim-dual-axis-scenario-quality-concrete-overlay-reset-validation-implementation.md`
- parent summary: `runs/m2464_paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_reset_validation/summary.json`
- reset/rerun/rollout/policy action/scenario-redesign execution/repair/training/replay/PPO in M2465: `false`
- ranking/winner selection in M2465: `false`
- actual-success improvement/paper/FW-vs-GRU/level3 self-ID/scenario-redesign-executed/training-repair/current-sim verdict claims: `false`

## Audit Result

M2465 accepts M2464 as complete reset-only evidence and classifies the failure
as a narrow scenario-sampling blocker in the R1 stable-AES overlay family.

```text
M2464 result_class: scenario_quality_concrete_overlay_reset_validation_fail
target_reset_count: 6
static_validation_pass_count: 6
static_validation_failure_count: 0
effective_env_config_written_count: 6
effective_env_config_outside_run_dir_count: 0
environment_reset_attempt_count: 6
environment_reset_success_count: 4
environment_reset_failure_count: 2
guardrail_violation_count: 1
failure_types_observed: scenario_sampling_failure
```

The failed guardrail is exactly reset success count:

```text
m2464_environment_reset_success_count:
  value: 4
  violation: true
  failure_mode_to_preserve: scenario_sampling_failure
```

All lineage, static-validation, effective-config, actor-contract, no-step,
no-policy, no-rollout, no-repair, no-training, no-ranking, no-winner, and
no-verdict guardrails passed.

## Row-Level Finding

M2464 reset outcomes by overlay family:

```text
R0_stable_avoidable / stable_feasibility_support:
  reset targets: 3
  reset successes: 3
  reset failures: 0

R1_aeb_infeasible_stable_aes / stable_aes_support:
  reset targets: 3
  reset successes: 1
  reset failures: 2
```

Failed rows:

```text
m2464_reset_target_004
source_candidate_id: m2455_stable_aes_support_001
eval_seed: 246403
failure_type: scenario_sampling_failure
failure_reason: RuntimeError: failed to sample an obstacle scenario matching the configured filters

m2464_reset_target_006
source_candidate_id: m2455_stable_aes_support_003
eval_seed: 246405
failure_type: scenario_sampling_failure
failure_reason: RuntimeError: failed to sample an obstacle scenario matching the configured filters
```

Successful R1 row:

```text
m2464_reset_target_005
source_candidate_id: m2455_stable_aes_support_002
eval_seed: 246404
observation_length: 72
observation_finite: true
obstacle_initialized: true
obstacle_label: aes_feasible
```

All three R1 rows share the same overlay hash:

```text
0688da6aec7f7314b7a46bbeb62af90313abddffea344d5d1ad1363f5acd678b
```

That means M2464 does not isolate whether the R1 blocker is a seed-fragile
randomized hidden-dynamics/sample-acceptance issue, an overly tight
`max_threshold_score`, an overly narrow obstacle geometry range, or an
interaction between the R1 overlay and the default hidden-dynamics
randomization. It is not evidence of actor-input contract failure.

## Interpretation Boundary

Accepted claim:

```text
M2464 reset-only validation cleanly reached environment reset attempts for all
six concrete-overlay rows, and failed only on two R1 stable-AES scenario
sampling rows.
```

Rejected claims:

```text
driver performance improvement
measured actual-success improvement
scenario redesign executed
repair/training success
support-policy/controller/checkpoint/scenario ranking
winner selection
paper-level result
finite-window vs GRU conclusion
level3 self-identification
current-sim verdict
```

This audit is consistent with the paper-route plans: reset-only scenario
readiness can improve scenario/task-quality infrastructure, but it does not
advance mechanism evidence for history dependence, GRU advantage, or
closed-loop self-identification.

## Decision

M2465 selects a bounded diagnostic implementation before any repair or measured
validation:

```text
m2466-paper-route-current-sim-dual-axis-scenario-quality-r1-reset-sampling-diagnostic-panel
```

The diagnostic should run reset-only sampler evidence over the R1 stable-AES
effective config family, preserving the P0 human-view contract and stopping
after reset. It should classify whether the failure is seed fragility,
hidden-dynamics randomization fragility, threshold strictness, obstacle geometry
range fragility, or a broader scenario-spec incompatibility. It must not step
the environment, execute policy actions, train, repair overlays in-place, rank
controllers, select winners, or make verdict claims.

M2465 does not route to measured rollout because reset admissibility is not yet
clean. It does not route directly to overlay repair because the current
evidence has only three R1 seeds and cannot distinguish repair levers without a
diagnostic panel.
