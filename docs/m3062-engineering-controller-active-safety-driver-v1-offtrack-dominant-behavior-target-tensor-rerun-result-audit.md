# M3062 Active Safety Driver v1 Offtrack-Dominant Behavior Target Tensor Rerun Result Audit

## Summary

- status: completed
- decision: `accept_m3061_target_tensor_rerun_claim_safe_route_to_m3063_branch_synthesis`
- audited milestone: `m3061-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-target-tensor-rerun-preflight`
- next route: `m3063-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-target-tensor-to-fitting-branch-synthesis`
- follow-up manifest: `experiments/manifests/m3063-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-target-tensor-to-fitting-branch-synthesis.json`

M3062 accepts M3061 as a complete and claim-safe raw-trace-backed target tensor
rerun preflight. M3061 consumed the M3060-accepted M3059 raw actor-view traces
and materialized trainer-side target tensor files while preserving actor
observation 72/action 3 direct `[steer, throttle, brake]`.

The accepted result is target tensor artifact completeness only. It does not
establish target quality, fitting readiness, fitted policy quality, repair
success, validation, current-sim verdict, driver performance, high-fidelity
validation, finite-window-vs-GRU evidence, paper evidence, full-driver
completion, or self-ID evidence.

## Evidence Summary

Accepted M3061 facts:

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

All M3061 target tensor row, file index, weight, actor-contract,
target-visibility, side-effect, claim-boundary, and gate artifacts are
accounted with zero failed rows. A file-level tensor audit confirms that the
masked recovery-window targets are not copies of the raw replay actions.

## Tensor Audit

M3061 writes bounded trainer-side files for 24 offtrack-dominant rows:

```text
observation_trace: float32 [T, 72]
raw_action_trace: float32 [T, 3]
next_observation_trace: float32 [T, 72]
target_action: float32 [T, 3]
target_action_mask: float32 [T, 3]
target_loss_weight: float32 [T, 3]
road_center_y_m: float32 [T]
near_road_center_y_m: float32 [T]
recovery_window: int32 [2]
raw_action_trace_used_as_target: bool false
```

The target rule is explicit and bounded:

```text
inside the final up-to-32-step terminal recovery window
estimate road-center offset from actor-visible left/right boundary points
damp steering with actor-visible body velocity and yaw-rate channels
suppress throttle and increase brake
keep all target labels and provenance trainer-side only
```

This makes the target tensor artifacts admissible for a fitting-admission
design review. It does not prove that fitting those targets will improve closed
loop safety.

## Actor And Claim Boundary Audit

M3061 preserves the deployment contract:

```text
actor observation shape: 72
actor action shape: 3
output components: steer;throttle;brake
base policy required at runtime: false
hidden oracle actor input detected: false
target labels actor-visible: false
target provenance actor-visible: false
TTC actor input required: false
source/route/outcome/progress/verdict labels actor-visible: false
environment reset/step/rollout run in M3061: false
local action search run: false
fitting/training/validation/ranking run: false
checkpoint mutation/promotion: false
```

The target tensor files are trainer-side artifacts. They do not alter actor
inputs, actor outputs, checkpoint lineage, runtime dependency surfaces, or
deployed action semantics.

## Supported Claims

M3062 supports only these bounded claims:

```text
M3061 materialized 24/24 raw-trace-backed trainer-side target tensor files
M3061 preserved actor observation 72 and action 3 direct [steer, throttle, brake]
M3061 used an explicit actor-visible road-center terminal recovery-window target rule
M3061 preserved raw replay actions for audit but did not use them as corrected recovery targets
M3061 kept target labels, provenance, TTC, source, route, outcome, progress, verdict, and oracle values outside actor inputs
M3063 branch synthesis is admitted as the only next route
```

These are artifact completeness, accounting, and claim-safety claims only.

## Rejected Claims

M3062 rejects:

```text
M3061 establishes target tensor quality: false
M3061 establishes fitting readiness by itself: false
M3061 fits, trains, validates, ranks, selects, promotes, or mutates a driver: false
M3061 proves offtrack recovery, repair success, validation success, current-sim verdict, or driver performance: false
M3061 produces high-fidelity, paper, finite-window-vs-GRU, full-driver, or self-ID evidence: false
```

## Failure Taxonomy Summary

```text
contract_violation: not observed for M3061 actor/target boundary artifacts
lineage_invalid: not observed for M3060/M3059/M3057/M3055/M3053 lineage
metric_artifact: not observed for M3061 row/file/gate accounting
scenario_sampling_failure: unresolved because M3061 reuses the 24-row offtrack denominator
behavior_regression: active risk until fitting and closed-loop measurement are audited
objective_overfit: active risk if future fitting over-optimizes terminal offtrack rows and ignores guards
proof_washout: active risk if future work hides the raw-trace/target-tensor boundary
seed_fragility: unresolved because no fresh scenario distribution or holdout route has been run
```

## Next Route

M3062 selects exactly one next route:

```text
m3063-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-target-tensor-to-fitting-branch-synthesis
```

M3063 must be synthesis-only. It must answer the required synthesis questions
and decide whether to continue to one claim-safe fitting-admission design route,
pivot to artifact repair or broader evidence, or stop. If it continues, the
follow-up is M3064 fitting-admission design, where loader, split, mask, weight,
guard, checkpoint side-effect, target-quality, and claim-boundary conditions can
be specified before any fitting run.

M3063 must not fit, train, validate, rank, select, promote, mutate checkpoints,
claim repair success, claim driver performance, make a current-sim or
high-fidelity verdict, produce paper evidence, run a finite-window-vs-GRU
comparison, evaluate a full ideal driver, or make self-ID claims.

## Boundary

M3062 is an audit-only milestone. It does not run reset, step, rollout, replay,
local-action search, target tensor fitting, training, validation, ranking,
promotion, high-fidelity simulation, finite-window-vs-GRU comparison, paper
evaluation, full-driver evaluation, or self-ID testing.
