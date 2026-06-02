# M2388 Paper-Route Current-Sim Dual-Axis Candidate Config Reset Validation Implementation

- status: failed
- result class: `current_sim_dual_axis_candidate_config_reset_validation_fail`
- manifest: `experiments/manifests/m2388-paper-route-current-sim-dual-axis-candidate-config-reset-validation-implementation.json`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_candidate_config_reset_validation.py`
- focused tests: `2 passed`
- summary: `runs/m2388_paper_route_current_sim_dual_axis_candidate_config_reset_validation/summary.json`
- command return code: `1`
- reset/rollout/policy action: `false/false/false`
- active config overwrite: `false`
- repair execution/training/replay/PPO: `false`
- ranking/winner/paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`
- next: `m2389-paper-route-current-sim-dual-axis-candidate-config-reset-validation-result-audit`

## Result

M2388 implemented a strict candidate config validator. The focused tests cover
both paths:

```text
synthetic env_config path:
  static validation passes, run-dir effective configs are written, and reset
  succeeds without environment steps.

missing env_config path:
  static validation passes, schema is classified incomplete, and reset is not
  attempted.
```

The real M2385 generated candidate configs took the second path:

```text
source_candidate_config_count: 54
static_validation_pass_count: 54
static_validation_failure_count: 0
schema_incomplete_candidate_count: 54
effective_config_written_count: 0
effective_config_outside_run_dir_count: 0
environment_load_attempt_count: 0
environment_reset_attempt_count: 0
environment_reset_success_count: 0
environment_step_count: 0
active_config_overwrite_count: 0
guardrail_violation_count: 0
```

Observed failure type:

```text
effective_config_materialization_failure
```

## Interpretation

This is a safe negative result. M2385 candidate configs are valid overlay
artifacts, but they do not contain a reset-ready `env_config`. The validator
therefore stopped before environment loading and reset.

This preserves the claim boundary:

```text
static candidate config safety passed
reset compatibility was not demonstrated
candidate configs were not activated
active config was not overwritten
no environment step or policy action occurred
no repair, training, ranking, paper, self-ID, or current-sim claim was made
```

## Failure Taxonomy

```text
static_schema_failure:
  not observed. The 54 generated candidate configs passed static checks.

path_safety_failure:
  not observed. No effective config was written outside the run dir.

effective_config_materialization_failure:
  observed for all 54 candidates because generated artifacts lack env_config.

sampler_incompatible_candidate:
  not tested. Reset was not attempted.

forbidden_execution_failure:
  not observed. The validator did not load environments, reset, step, repair,
  train, rank, or claim a verdict after schema incompleteness.
```

## Claim Boundary

Allowed claim:

```text
The M2388 validator safely rejects M2385 candidate configs as not reset-ready
because they lack effective env_config materialization.
```

Still blocked:

```text
reset compatibility
rollout or measured execution
repair execution
training/replay/PPO
support-policy or controller-family ranking
winner selection
scenario redesign executed claim
training repair success claim
paper-level benchmark evidence
finite-window vs GRU conclusion
level3 self-identification evidence
current-sim verdict
```

## Next

Route to a result audit:

```text
m2389-paper-route-current-sim-dual-axis-candidate-config-reset-validation-result-audit
```

The audit should decide whether to repair the candidate config schema by
materializing run-dir effective configs from a base env config, or to pivot away
from this branch if effective config materialization would become more local
artifact work without executable scenario-quality evidence.
