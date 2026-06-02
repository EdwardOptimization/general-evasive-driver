# M2392 Paper-Route Current-Sim Dual-Axis Effective Config Materialization Branch Synthesis

- status: completed
- synthesis decision: `continue`
- decision: `continue_to_effective_candidate_reset_validation_adapter_design`
- manifest: `experiments/manifests/m2392-paper-route-current-sim-dual-axis-effective-config-materialization-branch-synthesis.json`
- synthesis artifact: `docs/m2392-paper-route-current-sim-dual-axis-effective-config-materialization-branch-synthesis.md`
- synthesis window: `M2387-M2391`
- materialization rerun in M2392: `false`
- environment load/reset/step in M2392: `0/0/0`
- policy action in M2392: `false`
- active config overwrite in M2392: `false`
- repair execution/training/replay/PPO: `false`
- ranking/winner/paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Evidence Summary

M2387-M2391 converted overlay candidate configs into effective candidate pack
artifacts that are ready for a future reset-validation adapter design:

```text
M2387:
  designed static safety plus reset-only validation for M2385 generated
  candidate configs, but assumed candidates could become one standalone
  env_config each.

M2388:
  implemented the validator and failed closed:
    source_candidate_config_count: 54
    static_validation_pass_count: 54
    schema_incomplete_candidate_count: 54
    effective_config_written_count: 0
    environment_load_attempt_count: 0
    environment_reset_attempt_count: 0
    guardrail_violation_count: 0

M2389:
  audited the failure as schema incompleteness, not sampler incompatibility or
  unsafe execution.

M2390:
  corrected the schema: M2385 artifacts are overlay candidates, so effective
  configs should be pack-scoped scenario selections using M2356 reset-valid
  base pack env_config entries.

M2391:
  implemented and ran artifact-only materialization:
    source_candidate_config_count: 54
    static_validation_pass_count: 54
    effective_candidate_config_written_count: 54
    candidate_without_matching_scenarios_count: 0
    candidate_without_env_config_count: 0
    actor_contract_violation_count: 0
    selected_scenario_reference_count: 2049
    min/max selected_scenario_count: 6/180
    environment_load_attempt_count: 0
    environment_reset_attempt_count: 0
    guardrail_violation_count: 0
```

Actual capability changed:

```text
artifact capability:
  the repo can now join overlay repair candidates to reset-valid base pack
  scenario specs and write effective candidate pack artifacts under a run dir.
```

What did not change:

```text
driver behavior
reset validation of the effective candidate artifacts
rollout or measured execution
repair execution
training route
paper verdict
self-ID evidence
controller-family comparison
```

## Supported Claims

M2392 supports these bounded claims:

- M2388's fail-closed behavior prevented an invalid reset claim.
- The schema issue was correctly reclassified as overlay-vs-effective-config
  mismatch.
- M2356/M2359 provide legitimate base env_config lineage for reset-validation
  adapter design.
- M2391 generated 54 effective candidate pack artifacts with no unmatched
  candidates, no missing env_config, and no actor-contract violations.
- The local-search guard correctly stopped another ordinary result audit and
  required synthesis before a new validation-design step.
- A bounded effective candidate reset-validation adapter design is justified as
  the next process step.

## Falsified Claims

M2392 blocks or falsifies these claims:

- M2385 overlay candidate configs are standalone reset-ready env configs.
- M2388 demonstrated sampler compatibility.
- M2391 demonstrated reset compatibility.
- Effective candidate artifacts have been loaded into an environment.
- The offtrack repair route has improved driver behavior.
- Repair execution, training repair success, support-policy ranking, controller
  ranking, finite-window-vs-GRU conclusions, level3 self-ID, scenario redesign
  execution, paper-level results, or current-sim verdicts follow from this
  branch.

## Failure Taxonomy Summary

```text
scenario_sampling_failure:
  Still live. M2391 did not load or reset environments, so sampler
  compatibility remains unknown for effective candidate artifacts.

metric_artifact:
  Controlled. M2388 refused to manufacture reset metrics from overlay artifacts;
  M2391 reports only materialization counts and guardrail state.

lineage_invalid:
  Reduced. M2391 traces effective candidates to M2385 overlays and M2356
  reset-valid pack specs, with M2359 reset evidence for the base packs.

contract_violation:
  Not observed. M2391 selected scenario specs with actor_contract_violation_count 0.

objective_overfit:
  Not tested. Reward/curriculum overlays were not executed or optimized.

behavior_regression:
  Not tested. No policy behavior was changed or evaluated.

local_search_guard:
  Triggered correctly after M2391. Continuing with an ordinary audit would have
  exceeded the non-evidence milestone limit.
```

## Public Gate Overfit Risk

The public gate overfit risk remains moderate. This branch is still derived
from public M2362 outcome localization and repair-plan artifacts. That is
acceptable for task-quality infrastructure, but not for paper-level controller
or driver claims.

Risk controls preserved:

```text
no private holdout tuning
no active config overwrite
no environment load/reset in M2391/M2392
no policy action
no repair execution
no training/replay/PPO
no actor input change
no hidden/oracle feature injection
no profile-specific tuning
no support-policy or controller-family ranking
no winner selection
no paper/self-ID/current-sim verdict claim
```

## Paper-Route Axis Classification

```text
engineering driver performance:
  no new claim. No driver checkpoint is trained, modified, or evaluated.

mechanism evidence for history dependence:
  no new support. No wrong-history, reset-hidden, finite-window, or GRU
  comparison is run.

scenario/task-quality evidence:
  positive artifact evidence. The branch now has effective candidate pack
  artifacts that can be used by a future reset-validation adapter.

high-fidelity validation readiness:
  not ready. Current-sim effective candidates have not been reset-tested,
  measured, repaired, or ranked.

workflow or complexity reduction:
  positive. The harness prevented ordinary audit drift and forced a synthesis
  decision before another validation-design milestone.
```

## Actual Progress And Process Overhead

Process overhead was medium. The branch spent several milestones converting
repair-plan artifacts into executable-looking candidates, but M2388 exposed a
real schema gap and M2391 resolved it without violating guardrails.

The next milestone must create an executable validation route. Another
artifact-only repair step would be local search unless it directly reduces the
reset-validation adapter surface.

## Next Branch Decision

Decision:

```text
continue
```

Next milestone:

```text
m2393-paper-route-current-sim-dual-axis-effective-candidate-reset-validation-adapter-design
```

M2393 should design a reset-validation adapter for M2391 effective candidate
pack artifacts. It should specify:

```text
input artifacts:
  M2391 summary
  effective_candidate_config_rows.csv
  effective_candidate_scenario_rows.csv
  effective_candidate_configs/*.json

future reset scope:
  reset selected scenario env_config entries from effective candidate artifacts
  under a declared budget and duplicate-handling policy

required guardrails:
  no active config overwrite
  no policy action
  no environment step after reset
  no repair execution
  no training/replay/PPO
  no ranking/winner
  no paper/self-ID/current-sim verdict claim
```

M2393 itself must not load or reset environments. It is a design milestone only.
