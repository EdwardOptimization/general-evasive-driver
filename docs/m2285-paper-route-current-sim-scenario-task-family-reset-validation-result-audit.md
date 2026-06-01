# M2285 Paper-Route Current-Sim Scenario Task-Family Reset-Validation Result Audit

- status: completed
- decision: `current_sim_scenario_task_family_reset_validation_audit_route_to_sampling_and_lateral_sign_repair_design`
- manifest: `experiments/manifests/m2285-paper-route-current-sim-scenario-task-family-reset-validation-result-audit.json`
- parent result: `runs/m2284_paper_route_current_sim_scenario_task_family_reset_validation/summary.json`
- reset rerun in M2285: `false`
- rollout/measured execution in M2285: `false`
- policy actions executed in M2285: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Audit Result

M2284 is complete and guardrail clean, but reset validation fails:

```text
result_class: current_sim_scenario_task_family_reset_validation_fail
input_scenario_spec_count: 72
target_count_matches: true
reset_attempt_count: 72
reset_success_count: 12
reset_failure_count: 60
actor_contract_violation_count: 0
labels_enter_actor_input_count: 0
ranking_admissible_count: 0
lateral_bucket_mismatch_count: 66
guardrail_violation_count: 0
passes_public_reset_validation_gates: false
```

This is a scenario/config failure, not a controller-performance result.

## Reset-Sampling Failure

The reset failures are role-localized:

```text
R0_stable_avoidable: 12/12 reset successes
R1_aeb_infeasible_stable_aes: 0/12 reset successes
R2_handling_limit_drift_capable_avoidance: 0/12 reset successes
R3_recovery_after_limit: 0/12 reset successes
R4_unavoidable_mitigation: 0/12 reset successes
R5_hidden_dynamics_robustness: 0/12 reset successes
```

All 60 failures are:

```text
RuntimeError: failed to sample an obstacle scenario matching the configured filters
```

Interpretation:

```text
The v0 materializer produced config rows whose allowed label, distance/speed,
hidden dynamics, AEB infeasibility, and obstacle geometry filters are too
constrained for the current simulator sampler outside R0.
```

Therefore the next repair must be sampler-aware. It should not simply increase
`max_sample_attempts` or relax labels until the desired role meaning disappears.

## Lateral Sign Failure

M2282 anticipated a signed bucket risk. M2284 confirms it on successful R0
resets:

```text
successful centerline rows: 0/6 signed mismatches
successful left_offset rows: 3/3 signed mismatches
successful right_offset rows: 3/3 signed mismatches
```

The numeric offsets match the config, but the bucket names disagree with the
M2279/M2280 convention:

```text
positive obstacle_lateral_offset -> frame-left
negative obstacle_lateral_offset -> frame-right
```

Current materialized rows use the opposite sign:

```text
left_offset -> -1.2
right_offset -> +1.2
```

The summary-level `lateral_bucket_mismatch_count` is `66` because it includes
`60` rows where reset failed and actual lateral offset was unavailable, plus `6`
successful R0 left/right sign mismatches.

## Contract And Guardrails

The result preserves the actor boundary:

```text
actor_contract_violation_count: 0
labels_enter_actor_input_count: 0
ranking_admissible_count: 0
guardrail_violation_count: 0
```

No policy action, rollout, measured execution, training, replay, PPO, private
holdout, controller-family ranking, paper-level claim, finite-window-vs-GRU
verdict, or level3 self-ID claim was made.

## Decision

Route to one combined repair design:

```text
m2286-paper-route-current-sim-scenario-task-family-reset-sampling-and-lateral-sign-repair-design
```

The repair should handle both blockers together:

```text
1. correct the lateral bucket sign convention in the materializer;
2. redesign R1-R5 config generation to be sampler-aware and reset-validatable;
3. preserve the P0 actor contract and metadata-only role labels;
4. keep controller ranking and measured execution blocked until reset
   validation passes and is audited.
```

Do not split this into separate sign-only and sampler-only local repairs unless
the M2286 design proves one blocker must be isolated first.

## Blocked Routes

Blocked:

```text
direct measured rollout from the v0 scenario pack
policy action execution
training or PPO
controller-family ranking
winner selection
finite-window-vs-GRU verdict
paper-level result
level3 self-identification
high-fidelity validation as a replacement for current-sim reset repair
```

## Next

Pre-register:

```text
m2286-paper-route-current-sim-scenario-task-family-reset-sampling-and-lateral-sign-repair-design
```
