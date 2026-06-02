# M2389 Paper-Route Current-Sim Dual-Axis Candidate Config Reset Validation Result Audit

- status: completed
- decision: `schema_incomplete_reset_validation_failure_route_to_effective_config_schema_repair_design`
- manifest: `experiments/manifests/m2389-paper-route-current-sim-dual-axis-candidate-config-reset-validation-result-audit.json`
- audited summary: `runs/m2388_paper_route_current_sim_dual_axis_candidate_config_reset_validation/summary.json`
- audited doc: `docs/m2388-paper-route-current-sim-dual-axis-candidate-config-reset-validation-implementation.md`
- reset rerun in M2389: `false`
- rollout/measured execution in M2389: `false`
- repair execution/training/replay/PPO: `false`
- ranking/winner/paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Audit Summary

M2388 failed closed:

```text
result_class: current_sim_dual_axis_candidate_config_reset_validation_fail
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

The failure is not:

```text
static_schema_failure
path_safety_failure
sampler_incompatible_candidate
forbidden_execution_failure
```

The failure is:

```text
effective_config_materialization_failure
```

The M2385 candidate configs are valid overlay artifacts, but they are not
reset-ready effective env configs. They lack `env_config`, so the strict
validator correctly stopped before environment loading.

## Supported Claims

M2389 supports these bounded claims:

- The M2388 validator implementation is capable of fail-closed behavior.
- The M2385 generated candidate configs pass static safety checks.
- The generated candidate configs preserve reward/curriculum/guardrail
  references and claim boundaries.
- The generated candidate configs are not yet reset-ready because they lack
  effective `env_config`.
- No active config overwrite, environment step, policy action, repair,
  training, ranking, or paper/self-ID/current-sim claim occurred.

## Falsified Claims

M2389 blocks or falsifies these claims:

- M2385 candidate configs are reset-compatible.
- M2388 demonstrated sampler compatibility.
- M2388 demonstrated current-sim validation readiness.
- The branch can move directly to rollout, repair execution, training, or
  ranking.
- Schema incompleteness can be treated as reset success.
- Paper-level, finite-window-vs-GRU, level3 self-ID, training-repair, or
  current-sim verdict claims follow from this branch.

## Failure Taxonomy

```text
scenario_sampling_failure:
  Still live. Reset was not attempted, so sampler compatibility remains
  unknown.

metric_artifact:
  Controlled. The validator reported schema incompleteness rather than
  manufacturing reset metrics from overlay artifacts.

lineage_invalid:
  Not observed. M2388 uses M2385 generated candidate config artifacts and M2387
  design.

contract_violation:
  Not observed. No actor input, oracle feature, profile tuning, or active
  config overwrite violation occurred.

behavior_regression:
  Not tested. No policy behavior was changed or evaluated.

effective_config_materialization_failure:
  Observed. All 54 candidate configs lack env_config.
```

## Public Gate Overfit Risk

The public gate overfit risk remains moderate. This branch is still operating
on public M2362-derived repair artifacts. However, M2388 improved evidence
quality by preventing an invalid reset claim. The next step must either make
the candidate configs executable in a bounded, run-dir-only way or pivot.

## Decision

Decision:

```text
continue to bounded effective-config schema repair design
```

Next milestone:

```text
m2390-paper-route-current-sim-dual-axis-effective-config-schema-repair-design
```

M2390 should design how to materialize reset-ready effective configs by merging
generated candidate overlays with a legitimate base env config, under these
constraints:

```text
no active config overwrite
all effective configs under run dir
no reset in M2390
no rollout or policy action
no repair execution or training
no ranking or winner selection
no paper/self-ID/current-sim verdict claim
fail closed if no legitimate base env config lineage can be identified
```

If M2390 cannot define a bounded base-config lineage and effective-config
schema, the branch should pivot to complexity pruning or stop for user review.
