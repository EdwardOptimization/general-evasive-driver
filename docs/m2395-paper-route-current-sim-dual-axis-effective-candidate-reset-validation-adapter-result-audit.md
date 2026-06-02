# M2395 Paper-Route Current-Sim Dual-Axis Effective Candidate Reset Validation Adapter Result Audit

- status: completed
- decision: `effective_candidate_reset_validation_result_accepted_route_to_measured_validation_design`
- manifest: `experiments/manifests/m2395-paper-route-current-sim-dual-axis-effective-candidate-reset-validation-adapter-result-audit.json`
- parent implementation: `docs/m2394-paper-route-current-sim-dual-axis-effective-candidate-reset-validation-adapter-implementation.md`
- parent summary: `runs/m2394_paper_route_current_sim_dual_axis_effective_candidate_reset_validation_adapter/summary.json`
- reset rerun in M2395: `false`
- rollout/measured execution in M2395: `false`
- policy action executed in M2395: `false`
- repair execution/training/replay/PPO: `false`
- support-policy/controller-family ranking: `false`
- winner selected: `false`
- paper-level/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Audit Result

M2395 accepts the M2394 reset-only adapter pass as task-quality reset-readiness
evidence.

The accepted M2394 evidence is:

```text
result_class: current_sim_dual_axis_effective_candidate_reset_validation_adapter_pass
source_candidate_config_count: 54
candidate_scenario_reference_count: 2049
unique_reset_target_count: 350
static_validation_pass_count: 2049
static_validation_failure_count: 0
environment_load_attempt_count: 350
environment_reset_attempt_count: 350
environment_reset_success_count: 350
environment_reset_failure_count: 0
candidate_reset_pass_count: 54
candidate_reset_failure_count: 0
environment_step_count: 0
policy_action_executed: false
active_config_overwrite_count: 0
ranking_admissible_count: 0
winner_selected_count: 0
guardrail_violation_count: 0
failure_types_observed: []
```

Pack-level reset targets were balanced across the five source packs:

```text
baseline_reference_pack: 70
g_primary_pack: 70
h_primary_pack: 70
g_h_primary_pack: 70
gh_minimal_pack: 70
```

## Supported Claim

The bounded supported claim is:

```text
The M2391 effective candidate artifacts are reset-ready under the M2393
two-layer adapter: 2049 candidate-scenario references are statically valid, and
the 350 unique pack/scenario reset targets reset successfully without stepping
the environment or executing policy actions.
```

This is useful because M2388 failed closed on schema incompleteness. M2390-M2394
closed that schema/reset-readiness gap by treating each effective candidate as
an overlay plus M2356 reset-valid base-pack scenario selection, not as a single
standalone `env_config`.

## Claim Boundary

M2395 does not upgrade the result to closed-loop performance evidence.

Still blocked:

```text
rollout or measured execution
repair execution
training repair success
support-policy or controller-family ranking
winner selection
paper-level benchmark result
finite-window-vs-GRU conclusion
level3 self-identification
scenario redesign executed
current-sim verdict
```

The reason is simple: M2394 performed reset validation only. It executed:

```text
environment_step_count: 0
policy_action_executed: false
measured_rollout_started: false
```

Therefore no success rate, collision rate, offtrack rate, margin metric, driver
capability change, or paper-route verdict can be inferred from M2394/M2395.

## Failure Taxonomy

Observed failure types:

```text
none
```

Monitored failure classes were:

```text
scenario_sampling_failure
metric_artifact
lineage_invalid
contract_violation
behavior_regression
```

No monitored failure was observed in the parent result. The audit specifically
rejects a `metric_artifact` interpretation where reset-readiness is treated as
measured closed-loop behavior.

## Route Decision

Decision:

```text
effective_candidate_reset_validation_result_accepted_route_to_measured_validation_design
```

Next milestone:

```text
m2396-paper-route-current-sim-dual-axis-effective-candidate-measured-validation-design
```

M2396 should design a bounded measured-validation protocol over the reset-ready
effective candidate artifacts. It should freeze the denominator, input
artifacts, controller/checkpoint source, metrics, guardrails, duplicate policy,
and claim boundary before any measured rollout.

M2396 must not run rollout, execute repair, train, rank, select a winner, or
make paper/self-ID/current-sim verdict claims.
