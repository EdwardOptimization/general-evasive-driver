# M2380 Paper-Route Current-Sim Dual-Axis Repair Plan Materialization Branch Synthesis

- status: completed
- synthesis decision: `continue`
- decision: `continue_to_bounded_config_patch_application_design`
- manifest: `experiments/manifests/m2380-paper-route-current-sim-dual-axis-repair-plan-materialization-branch-synthesis.json`
- synthesis artifact: `docs/m2380-paper-route-current-sim-dual-axis-repair-plan-materialization-branch-synthesis.md`
- synthesis window: `M2375-M2379`
- reset/rollout/policy action in M2380: `false`
- measured execution in M2380: `false`
- active config overwrite in M2380: `false`
- config patch application in M2380: `false`
- repair execution/training/replay/PPO in M2380: `false`
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

M2375-M2379 converted the audited offtrack/guardrail repair specs into a clean
overlay config-patch artifact chain:

```text
M2375:
  materialized repair-plan artifacts from M2371 repair specs:
    reward_delta_row_count 54
    curriculum_weight_row_count 54
    guardrail_constraint_row_count 284
    mixed_guarded_constraint_row_count 18
    guardrail_violation_count 0

M2376:
  accepted the repair-plan artifacts and blocked direct repair execution,
  training, ranking, and paper interpretation.

M2377:
  designed overlay-only config-patch materialization from repair-plan artifacts.

M2378:
  materialized config-patch artifacts:
    reward_config_patch_row_count 162
    curriculum_config_patch_row_count 54
    guardrail_config_patch_row_count 284
    target namespaces:
      candidate_reward_overlay 162
      candidate_curriculum_overlay 54
      candidate_guardrail_overlay 284
    guardrail_violation_count 0

M2379:
  accepted the config-patch artifacts, but routed to branch synthesis because
  local-search guard blocks another narrow application-design milestone without
  synthesis.
```

This branch improved task-quality infrastructure. It did not change the driver,
execute repair, apply config patches, run validation, or produce paper-level
controller evidence.

## Supported Claims

M2380 supports these bounded claims:

- The repair-plan artifacts from M2375 are internally consistent and guardrail
  clean.
- The M2378 overlay config-patch artifacts are internally consistent and
  guardrail clean.
- Reward, curriculum, collision, R4, diagnostic, and mixed guarded constraints
  remained separated through the artifact chain.
- All generated patch rows target candidate overlay namespaces rather than the
  active scenario config.
- The workflow guard correctly stopped local application-design drift and
  forced branch synthesis.
- A bounded candidate config-patch application design is justified as the next
  process step.

## Falsified Claims

M2380 blocks or falsifies these claims:

- The config patches have been applied.
- The active scenario config has been overwritten.
- Repair execution has started.
- Training repair success has been demonstrated.
- Scenario redesign has been executed.
- The measured offtrack failure mode has been fixed.
- Support policies, controller families, finite-window, or GRU variants can be
  ranked from these artifacts.
- Level3 self-identification or finite-window-vs-GRU conclusions follow from
  this branch.
- Another narrow application-design/materialization step should proceed without
  synthesis.

## Failure Taxonomy Summary

```text
scenario_sampling_failure:
  Still live. M2375-M2379 did not run reset, rollout, or measured validation.

metric_artifact:
  Reduced for this route. Offtrack repair targets, mixed collision guardrails,
  R4 mitigation semantics, and diagnostic no-ranking rows remain separated.

contract_violation:
  No actor-input, hidden/oracle feature, or active-config overwrite violation
  is present in M2375-M2379.

objective_overfit:
  Not tested. No reward/training objective was executed.

behavior_regression:
  Not tested. No policy behavior was changed or evaluated.

local_search_guard:
  Triggered correctly. The branch accumulated repair-plan/config-patch
  artifacts and audits without new capability data, so synthesis was required
  before any application-design continuation.
```

## Public Gate Overfit Risk

The public gate overfit risk is moderate.

The branch derives repair and patch artifacts from the public measured panel
and its public localization/guardrail surfaces. This is acceptable for
engineering task-quality repair planning. It is not paper-level performance
evidence and must not be used for controller-family ranking.

Risk controls preserved by M2375-M2379:

```text
no private holdout tuning
no active config overwrite
no config patch application
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
  positive artifact evidence. The branch turns localized offtrack/guardrail
  failures into candidate repair-plan and config-patch artifacts with clean
  claim boundaries.

high-fidelity validation readiness:
  not ready. Current-sim candidate patches have not been applied to candidate
  configs, reset-tested, or measured.

workflow or complexity reduction:
  positive. The local-search guard stopped another design-only step and forced
  this synthesis; the next step is explicitly bounded.
```

## Actual Progress And Process Overhead

Actual capability changed:

```text
artifact capability only:
  the repo can now derive overlay config-patch artifacts from measured
  offtrack/guardrail repair plans.
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

Process overhead was medium. M2375-M2379 had useful artifact progression, but
the branch was close to becoming a chain of local application-design steps.
The guardrail stop was therefore correct.

## Next Branch Decision

Decision:

```text
continue
```

Next milestone:

```text
m2381-paper-route-current-sim-dual-axis-offtrack-guardrail-config-patch-application-design
```

M2381 should design how to materialize candidate config copies from M2378
overlay artifacts. It should not apply patches in M2381. The design must keep
these routes blocked:

```text
active config overwrite
environment reset/rollout/measured execution
repair execution
training/replay/PPO
actor input change
hidden/oracle feature injection
profile-specific tuning
support-policy or controller-family ranking
winner selection
paper-level claim
finite-window vs GRU conclusion
level3 self-identification evidence
scenario redesign executed
training repair success
current-sim verdict
```

## Blocked Routes

Blocked after synthesis:

```text
direct active config overwrite
direct config patch application without design
direct reset validation without candidate config materialization
direct training from repair-plan/config-patch artifacts
direct scenario redesign execution
direct controller-family or support-policy ranking
direct paper-route verdict
direct self-ID claim
another narrow repair-plan materialization branch milestone without the M2380
synthesis decision
```

## Claim Boundary

M2380 may claim only:

```text
The M2375-M2379 repair-plan materialization branch has been synthesized and
should continue to bounded config-patch application design.
```

Still blocked:

```text
repair execution
training repair success
scenario redesign executed
controller-family ranking
support-policy ranking
winner selection
paper-level benchmark evidence
finite-window vs GRU conclusion
level3 self-identification evidence
current-sim verdict
```
