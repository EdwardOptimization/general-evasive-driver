# M2386 Paper-Route Current-Sim Dual-Axis Candidate Config Generation Branch Synthesis

- status: completed
- synthesis decision: `continue`
- decision: `continue_to_bounded_candidate_config_safety_validation_design`
- manifest: `experiments/manifests/m2386-paper-route-current-sim-dual-axis-candidate-config-generation-branch-synthesis.json`
- synthesis artifact: `docs/m2386-paper-route-current-sim-dual-axis-candidate-config-generation-branch-synthesis.md`
- synthesis window: `M2381-M2385`
- reset/rollout/policy action in M2386: `false`
- measured execution in M2386: `false`
- active config overwrite in M2386: `false`
- candidate config loading in M2386: `false`
- repair execution/training/replay/PPO in M2386: `false`
- support-policy ranking claim made: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`
- scenario redesign executed claim made: `false`
- training repair success claim made: `false`
- current-sim verdict claim made: `false`

## Evidence Summary

M2381-M2385 converted the audited overlay config-patch artifacts into
run-dir-only candidate config artifacts:

```text
M2381:
  designed an artifact-only application-plan materializer.
  active config overwrite and patch application were blocked.

M2382:
  materialized application-plan artifacts:
    candidate_application_spec_count 54
    reward/curriculum/guardrail patch references 162/54/284
    mixed_guarded_candidate_requirement_count 18
    guardrail_violation_count 0

M2383:
  accepted M2382 application-plan artifacts and blocked direct config
  generation, reset validation, repair execution, training, and ranking.

M2384:
  designed run-dir-only candidate config generation and required branch
  synthesis after M2385.

M2385:
  materialized candidate config artifacts:
    candidate_config_file_written_count 54
    candidate_config_files_outside_run_dir_count 0
    reward/curriculum/guardrail references 162/54/284
    mixed_guarded_candidate_requirement_count 18
    guardrail_violation_count 0
```

The branch improved task-quality infrastructure. It did not change the driver,
load a candidate config, execute repair, run validation, train, rank, or
produce paper-level controller evidence.

## Supported Claims

M2386 supports these bounded claims:

- The application-plan artifacts from M2382 are internally consistent and
  guardrail clean.
- M2385 generated one run-dir-only candidate config file for each of the 54
  candidate application specs.
- Reward, curriculum, global guardrail, and mixed collision guardrail
  references remained present in every generated candidate config.
- The candidate configs were generated as artifacts only; they were not loaded
  into an environment and did not overwrite an active config.
- The workflow guard correctly stopped the branch after candidate config
  generation and forced synthesis before another validation-design step.
- A bounded candidate config safety/reset-validation design is justified as the
  next process step.

## Falsified Claims

M2386 blocks or falsifies these claims:

- The generated candidate configs have been activated.
- The active scenario config has been overwritten.
- A reset, rollout, or measured validation has been run on generated candidate
  configs.
- Repair execution has started.
- Training repair success has been demonstrated.
- Scenario redesign has been executed.
- The measured offtrack failure mode has been fixed.
- Support policies, controller families, finite-window, or GRU variants can be
  ranked from these artifacts.
- Level3 self-identification or finite-window-vs-GRU conclusions follow from
  this branch.
- Another narrow generation/audit step should proceed without synthesis.

## Failure Taxonomy Summary

```text
scenario_sampling_failure:
  Still live. M2381-M2385 did not run reset, rollout, or measured validation.

metric_artifact:
  Reduced for this route. Candidate configs preserve reward, curriculum,
  global guardrail, and mixed guarded collision references, but no metric has
  been measured on the generated configs.

lineage_invalid:
  Not observed. M2385 traces back to M2382 application-plan artifacts and M2384
  generation design.

contract_violation:
  No actor-input, hidden/oracle feature, profile-specific tuning, or active
  config overwrite violation is present in M2381-M2385.

objective_overfit:
  Not tested. No reward/training objective was executed.

behavior_regression:
  Not tested. No policy behavior was changed or evaluated.

local_search_guard:
  Triggered correctly. The branch accumulated application-plan and generated
  config artifacts without new capability data, so synthesis is required before
  validation design.
```

## Public Gate Overfit Risk

The public gate overfit risk is moderate.

The branch derives repair, patch, application, and generated config artifacts
from the public M2362 measured panel and public localization/guardrail route.
This is acceptable for engineering task-quality repair planning. It is not
paper-level performance evidence and must not be used for controller-family
ranking.

Risk controls preserved by M2381-M2385:

```text
no private holdout tuning
no active config overwrite
no candidate config loading
no reset or rollout
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
  positive artifact evidence. The branch turns application-plan rows into
  concrete candidate config artifacts with clean claim boundaries.

high-fidelity validation readiness:
  not ready. Current-sim candidate configs have not been reset-tested,
  measured, repaired, or ranked.

workflow or complexity reduction:
  positive. The local-search guard stopped further narrow generation/audit work
  and forced a route decision.
```

## Actual Progress And Process Overhead

Actual capability changed:

```text
artifact capability only:
  the repo can now generate candidate config JSON artifacts from audited
  application-plan rows without touching the active config.
```

What did not change:

```text
driver behavior
scenario execution
repair execution
training route
paper verdict
self-ID evidence
controller-family comparison
```

Process overhead was medium. The artifact chain was justified because it kept
active config overwrite and claim boundaries clean. Continuing with another
ordinary audit would be local search; the next step must either design bounded
validation or pivot.

## Next Branch Decision

Decision:

```text
continue
```

Next milestone:

```text
m2387-paper-route-current-sim-dual-axis-candidate-config-safety-validation-design
```

M2387 should design a bounded safety/reset-validation protocol for the generated
candidate configs. M2387 itself must not load configs, reset environments, run
rollouts, execute repair, train, rank, select a winner, or make paper/self-ID
claims. The design should explicitly define:

```text
source candidate config inventory
static schema/path safety checks
allowed future reset-only validation scope
blocked future rollout/training/ranking routes
failure taxonomy for sampler incompatibility or guardrail violations
route to an implementation milestone only if validation scope is bounded
```

The branch should pivot instead of continuing if the next validation design
would only add more artifact local search without producing executable
scenario-quality evidence.
