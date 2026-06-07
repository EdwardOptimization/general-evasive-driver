# M3063 Active Safety Driver v1 Offtrack-Dominant Behavior Target Tensor To Fitting Branch Synthesis

## Summary

- status: completed
- synthesis decision: `continue`
- decision: `continue_to_m3064_fitting_admission_design`
- branch: `active_safety_driver_v1_offtrack_dominant_behavior_repair`
- parent audit: `docs/m3062-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-target-tensor-rerun-result-audit.md`
- next route: `m3064-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-fitting-admission-design`
- follow-up manifest: `experiments/manifests/m3064-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-fitting-admission-design.json`

M3063 synthesizes the M3053-M3062 active-safety offtrack behavior branch after
the local-search guard blocked another ordinary process-only milestone. The
branch has advanced from behavior-negative closed-loop measurement to
claim-safe trainer-side target artifacts for a deployable direct-action
recovery/reflex layer. It has not yet produced fitted policy quality,
closed-loop repair evidence, validation evidence, driver-performance evidence,
current-sim verdict evidence, high-fidelity evidence, paper evidence,
finite-window-vs-GRU evidence, full-driver evidence, or self-ID evidence.

The correct next step is one bounded fitting-admission design milestone, M3064.
M3064 may specify loader, split, mask, weight, target-quality, guard,
checkpoint side-effect, and claim-boundary requirements for a later offline
fitting preflight. M3064 must not fit, train, validate, rank, select, promote,
mutate checkpoints, or claim driver performance.

M3063 does not run reset, step, rollout, replay, local-action search, target
tensor fitting, training, validation, ranking, promotion, high-fidelity
simulation, finite-window-vs-GRU comparison, paper-route evaluation,
full-driver evaluation, or self-ID testing.

## Evidence Summary

M3053 established the behavior target-source and guard surface:

```text
status_pass: true
gate_matrix_pass: true
required_artifacts_present: true
behavior target-source rows: 24
actor-contract guard rows: 8
claim-boundary rows: 12
gate rows: 18
actor contract: observation 72 / action 3 direct [steer, throttle, brake]
hidden oracle actor input detected: false
target labels/provenance actor-visible: false / false
TTC actor input required: false
fitting/training/validation/ranking/checkpoint mutation: false
driver-performance/current-sim/high-fidelity/paper/self-ID claims: false
```

M3055 converted that surface into a direct-action fitting contract:

```text
status_pass: true
gate_matrix_pass: true
required_artifacts_present: true
output_semantics: direct_action
observation/action shape: 72 / 3
output components: [steer, throttle, brake]
base_policy_required_at_runtime: false
fitting contract rows: 1
loss family rows: 6
row admission rows: 5
actor-contract guard rows: 9
target-visibility guard rows: 5
side-effect guard rows: 16
claim-boundary rows: 13
fitting/training/validation/ranking/checkpoint mutation: false
driver-performance/current-sim/high-fidelity/paper/self-ID claims: false
```

M3057 made the first target tensor attempt fail closed instead of inventing
targets without raw actor-view traces:

```text
status_pass: false
gate_matrix_pass: false
required_artifacts_present: true
result_class: active_safety_driver_v1_offtrack_behavior_target_tensor_materialization_fail_closed_missing_raw_actor_view_traces
behavior target tensor rows: 24
raw actor-view traces required/available/missing: 24 / 0 / 24
numeric target tensors materialized: 0
target tensor weight rows: 6
actor/target-visibility/side-effect/claim guards preserved
actor contract: observation 72 / action 3 direct [steer, throttle, brake]
```

M3059 closed the M3057 blocker by capturing raw actor-view traces for the same
denominator:

```text
status_pass: true
gate_matrix_pass: true
required_artifacts_present: true
raw trace index rows: 24
raw traces persisted/missing: 24 / 0
total_steps: 2692
trace step counts match M3050: true
actor-contract guard rows: 20
claim-boundary rows: 17
actor contract: observation 72 / action 3 direct [steer, throttle, brake]
fitting/training/validation/ranking/checkpoint mutation: false
driver-performance/current-sim/high-fidelity/paper/self-ID claims: false
```

M3061 reran target tensor materialization from the raw traces and produced the
first complete trainer-side numeric target tensor set:

```text
status_pass: true
gate_matrix_pass: true
required_artifacts_present: true
result_class: active_safety_driver_v1_offtrack_behavior_target_tensor_rerun_preflight_pass
behavior target tensor rows: 24
target tensor file index rows: 24
target tensor files: 24
target tensors missing: 0
target tensor weight rows: 6
actor-contract guard rows: 16
target-visibility guard rows: 6
side-effect guard rows: 16
claim-boundary rows: 17
gate rows: 37
masked recovery steps total: 768
target loss weight sum total: 1344.0000114440918
target rule: actor_visible_road_center_terminal_recovery_window
target rule uses actor-visible observation: true
raw action trace used as target: false
actor contract: observation 72 / action 3 direct [steer, throttle, brake]
```

M3062 audited M3061 and accepted only artifact completeness and claim safety:

```text
decision: accept_m3061_target_tensor_rerun_claim_safe_route_to_m3063_branch_synthesis
accepted: 24/24 raw-trace-backed trainer-side target tensor files
accepted: actor-visible road-center terminal recovery-window target rule
accepted: raw replay actions preserved for audit but not used as corrected targets
accepted: target labels, provenance, TTC, source, route, outcome, progress, verdict, and oracle values outside actor inputs
rejected: target tensor quality
rejected: fitting readiness by itself
rejected: fitted policy quality
rejected: repair success
rejected: validation, ranking, promotion, driver performance, current-sim verdict
rejected: high-fidelity, paper, finite-window-vs-GRU, full-driver, self-ID evidence
next route admitted: M3063 branch synthesis before fitting admission
```

Across M3053-M3062, the branch changed project capability from a negative
closed-loop measurement and residual-only repair dead end into a bounded
trainer-side dataset and contract candidate for a direct obs72-to-action3
active-safety reflex layer. That is real engineering progress, but it remains
pre-fitting artifact progress.

## Supported Claims

M3063 supports only these bounded claims:

```text
M3053 materialized a 24-row offtrack-dominant behavior target-source surface.
M3055 materialized a claim-safe direct-action obs72-to-action3 fitting contract.
M3057 correctly failed closed when raw actor-view traces were missing.
M3059 captured 24/24 raw actor-view traces for the M3057 blocker denominator.
M3061 materialized 24/24 raw-trace-backed trainer-side target tensor files.
M3061 used an explicit actor-visible road-center terminal recovery-window rule.
M3061 did not use raw replay actions as corrected recovery targets.
M3053-M3062 preserved actor observation 72 and action 3 direct [steer, throttle, brake].
M3053-M3062 kept target labels, target provenance, TTC, source, route, outcome, progress, verdict, and oracle values out of actor inputs.
M3064 fitting-admission design is the only admitted next route.
```

These claims are artifact completeness, contract-safety, lineage, and route
decision claims. They do not imply that the targets are good enough to fit, or
that a fitted policy will improve offtrack recovery.

## Falsified Claims

M3063 rejects these claims:

```text
M3061 target tensor artifact completeness is equivalent to target tensor quality.
M3061 target tensor artifact completeness is equivalent to fitting readiness.
The branch has already fitted, trained, validated, ranked, selected, promoted, or mutated a driver.
The branch has proved offtrack repair success or driver performance.
The branch has produced a current-sim verdict, high-fidelity result, paper result, finite-window-vs-GRU result, full-driver result, or self-ID result.
The next legal step is direct fitting without first specifying admission boundaries.
Another ordinary process-only milestone is justified before synthesis.
Raw replay actions can be treated as corrected recovery targets.
```

The branch also preserves the M3052 negative measurement: the earlier
actuation-aware residual cleanup removed final-action clipping but did not
improve same-denominator success, collision, offtrack, or speed-floor outcomes.
M3053-M3062 have not yet measured a closed-loop behavior repair.

## Failure Taxonomy Summary

```text
contract_violation: not observed in actor observation/action, target visibility, or claim-boundary guards.
lineage_invalid: not observed; M3053-M3062 form a traceable chain from target-source rows through fitting contract, raw traces, target tensors, and audits.
metric_artifact: not observed for row/file/gate accounting; still active as a risk if future reports convert artifact completeness into performance.
scenario_sampling_failure: unresolved because the branch remains on the 24-row offtrack-dominant denominator.
behavior_regression: unresolved and active until a later fitted policy is measured closed loop.
objective_overfit: active risk because terminal offtrack target windows can overfit the public denominator or optimize recovery shape without preserving collision/speed/success guards.
proof_washout: active risk if future fitting hides the trainer-side target/provenance boundary or drops raw-trace auditability.
seed_fragility: unresolved because no fresh scenario distribution, private holdout, or high-fidelity surface has been run.
process_overhead: medium; the branch needed target-source, contract, fail-closed tensor, raw-trace, rerun, and audits before fitting admission, and the local-search cadence now requires synthesis before continuing.
```

## Public Gate Overfit Risk

The overfit risk is medium, not low:

```text
fixed denominator: 24 offtrack-dominant rows
fixed public surfaces: behavior target-source rows, raw trace rows, target tensor rows, guard rows, and gate matrix rows
positive evidence so far: artifact completeness and contract safety
missing evidence: target quality, offline fitting behavior, closed-loop recovery, holdout robustness, collision preservation, speed-floor preservation, and high-fidelity transfer
```

Future milestones must treat public gate rows as admission guards, not as the
objective itself. The next route must explicitly separate:

```text
loader/split correctness from fitting success
mask/weight semantics from target quality
target tensor artifact completeness from policy behavior
offline fitting loss from closed-loop safety
same-denominator repair from generalization or promotion
engineering active-safety evidence from self-ID or paper-route evidence
```

This matches the post-M2470 route split: the engineering controller route can
advance a deployable active-safety reflex layer, while self-ID/GRU/paper
evidence remains auxiliary and separately falsifiable.

## Next Branch Decision

M3063 chooses:

```text
decision: continue_to_m3064_fitting_admission_design
synthesis_decision: continue
next route: m3064-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-fitting-admission-design
follow-up manifest: experiments/manifests/m3064-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-fitting-admission-design.json
```

The continue decision is justified because M3053-M3062 changed the evidence
surface enough to support one bounded fitting-admission design:

```text
the actor input/output contract is explicit and preserved
the runtime output is direct [steer, throttle, brake]
the branch no longer needs a base policy at runtime for this fitting contract
the target tensors are materialized, file-indexed, masked, weighted, and guarded
the target rule is explicit and actor-visible
the raw replay action trace is preserved for audit and not used as target
the claim boundaries are strong enough to design admission without overclaiming
```

The continue decision is not a promotion and not a fitting-readiness claim.
M3064 must decide exactly one of:

```text
admit one bounded offline fitting preflight with explicit loader/split/mask/weight/guard/checkpoint-side-effect/target-quality boundaries
pivot to artifact repair if the admission boundary is incomplete
pivot to branch synthesis or stop if fitting admission would weaken actor or claim boundaries
stop if the only available next action would be another process-only artifact with no new evidence surface
```

M3064 must preserve these hard boundaries:

```text
actor observation shape: 72
actor action shape: 3
output components: steer; throttle; brake
hidden oracle/TTC actor inputs: forbidden
target labels/provenance/source/route/outcome/progress/verdict/paper labels as actor inputs: forbidden
raw replay actions as corrected recovery targets: forbidden
fitting/training/validation/ranking/promotion/checkpoint mutation in M3064: forbidden
repair-success/driver-performance/current-sim/high-fidelity/paper/finite-window-vs-GRU/full-driver/self-ID claims in M3064: forbidden
```

## Rejected Immediate Routes

M3063 rejects these immediate routes:

```text
direct offline fitting without fitting-admission design
rollout validation, ranking, promotion, or winner selection
another process-only target artifact milestone before deciding admission
high-fidelity validation readiness claim from current target tensor artifacts
paper-route finite-window-vs-GRU or self-ID conclusion
target tensor quality claim before target-quality and fitting-admission boundaries are specified
```

## Boundary

M3063 is a synthesis and route-decision milestone only. It integrates M3053-M3062
evidence, resets the local-search cadence with a `continue` decision, and opens
exactly one next route, M3064 fitting-admission design. It does not claim that
the active-safety driver objective is solved.
