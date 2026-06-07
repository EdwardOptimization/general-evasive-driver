# M3064 Active Safety Driver v1 Offtrack-Dominant Behavior Fitting Admission Design

## Summary

- status: completed
- decision: `admit_m3065_bounded_direct_action_fitting_preflight_without_validation_or_promotion`
- manifest: `experiments/manifests/m3064-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-fitting-admission-design.json`
- parent synthesis: `docs/m3063-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-target-tensor-to-fitting-branch-synthesis.md`
- parent audit: `docs/m3062-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-target-tensor-rerun-result-audit.md`
- parent target tensor run: `runs/m3061_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_target_tensor_rerun_preflight/summary.json`
- follow-up manifest: `experiments/manifests/m3065-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-bounded-direct-action-fitting-preflight.json`
- next route: `m3065-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-bounded-direct-action-fitting-preflight`

M3064 admits exactly one bounded offline fitting preflight for a deployable
direct-action active-safety reflex layer. The admitted route is M3065, which may
consume the M3062-accepted M3061 target tensor artifacts and M3055 fitting
contract to fit or fail closed one offline `obs72 -> action3` candidate artifact.

M3064 remains design-only. It does not fit, train, validate, rank, select,
promote, mutate checkpoints, run the environment, claim repair success, claim
driver performance, make a current-sim or high-fidelity verdict, produce paper
evidence, compare finite-window and GRU controllers, evaluate a full driver, or
make self-ID claims.

## Evidence Review

M3063 admits M3064 because M3053-M3062 moved the branch from behavior-negative
measurement into a claim-safe trainer-side target tensor surface:

```text
M3055 fitting contract:
  output_semantics: direct_action
  observation/action shape: 72 / 3
  output components: steer;throttle;brake
  base_policy_required_at_runtime: false
  fitting run: false

M3061 target tensor rerun:
  status_pass: true
  gate_matrix_pass: true
  required_artifacts_present: true
  behavior target tensor rows: 24
  target tensor file index rows: 24
  target tensor files: 24
  target tensors missing: 0
  target tensor weight rows: 6
  gate rows: 37
  masked recovery steps total: 768
  target loss weight sum total: 1344.0000114440918
  target rule: actor_visible_road_center_terminal_recovery_window
  target rule uses actor-visible observation: true
  raw action trace used as target: false
  actor contract: observation 72 / action 3 direct [steer, throttle, brake]
```

The M3061 tensor files contain the exact tensors needed for a bounded offline
direct-action fitting preflight:

```text
observation_trace: float32 [T,72]
raw_action_trace: float32 [T,3]
next_observation_trace: float32 [T,72]
target_action: float32 [T,3]
target_action_mask: float32 [T,3]
target_loss_weight: float32 [T,3]
road_center_y_m: float32 [T]
near_road_center_y_m: float32 [T]
recovery_window: int32 [2]
raw_action_trace_used_as_target: bool false
```

The 24-row denominator remains fixed and public:

```text
binding_role counts: candidate 14, parent 10
task_family counts: T4 14, T5 10
termination reason: off_track 24
masked recovery steps: 768
```

This evidence is sufficient to attempt one bounded offline fitting artifact. It
is not sufficient to claim target quality, fitting readiness as a broad state,
closed-loop recovery, collision preservation, speed-floor preservation,
generalization, high-fidelity transfer, or deployed driver performance.

## Admission Boundary

M3064 distinguishes six states:

```text
target tensor artifact completeness: accepted
actor/action contract safety: accepted
direct-action fitting preflight admission: true
target quality validation: false
closed-loop validation or driver-performance readiness: false
promotion or deployment readiness: false
```

The accepted artifacts are enough for M3065 because:

```text
the runtime contract is direct obs72-to-action3 with no base policy dependency
each row has actor-visible observations and trainer-side target actions
mask and weight tensors identify the terminal recovery-window fitting samples
raw replay actions are preserved for audit and explicitly not used as targets
target labels and target provenance remain actor-invisible
side-effect and claim-boundary rows prohibit checkpoint mutation and overclaiming
```

The same artifacts are not enough to interpret M3065 loss decrease as target
quality or driver improvement. M3065 may only report whether a bounded offline
candidate artifact was written, whether loader/split/mask/weight/accounting
guards passed, and whether it registered a result audit.

## M3065 Preflight Contract

M3065 must consume:

```text
docs/m3064-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-fitting-admission-design.md
docs/m3063-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-target-tensor-to-fitting-branch-synthesis.md
docs/m3062-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-target-tensor-rerun-result-audit.md
runs/m3061_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_target_tensor_rerun_preflight/summary.json
runs/m3061_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_target_tensor_rerun_preflight/behavior_target_tensor_rows.csv
runs/m3061_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_target_tensor_rerun_preflight/target_tensor_file_index_rows.csv
runs/m3061_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_target_tensor_rerun_preflight/target_tensor_weight_rows.csv
runs/m3061_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_target_tensor_rerun_preflight/target_tensors/*.npz
runs/m3055_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_fitting_contract_materialization_preflight/fitting_contract_rows.csv
runs/m3055_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_fitting_contract_materialization_preflight/loss_family_rows.csv
```

M3065 may:

```text
build a trainer-side fitting dataset from observation_trace and target_action
use target_action_mask and target_loss_weight to choose the fitting denominator
create deterministic fit/internal-accounting split rows without claiming validation
fit one bounded direct-action obs72-to-action3 candidate artifact
write fitting_dataset_rows.csv, split_rows.csv, mask_weight_rows.csv, fitting_loss_trace_rows.csv, actor_input_exclusion_rows.csv, checkpoint_side_effect_guard_rows.csv, target_quality_boundary_rows.csv, claim_boundary_rows.csv, gate_matrix.csv, summary.json, run_state.json, and a doc artifact
write candidate_direct_action_reflex_layer.npz only if all fitting-contract gates pass
register M3066 result audit
```

M3065 must not:

```text
use target labels, target provenance, source, route, outcome, progress, verdict, paper labels, TTC, hidden oracle values, or future-target values as actor inputs
use raw replay actions as corrected recovery targets
convert guard-only loss families into positive target-action rows
run environment reset, step, rollout, replay, policy validation, ranking, winner selection, private holdout, high-fidelity simulation, finite-window-vs-GRU comparison, paper evaluation, full-driver evaluation, or self-ID testing
mutate, replace, rank, select, save over, or promote parent checkpoints
claim target quality, repair success, driver performance, current-sim verdict, high-fidelity validation, paper evidence, finite-window-vs-GRU evidence, full-driver completion, or self-ID evidence
```

## Loader, Split, Mask, And Weight Rules

M3065 loader rules:

```text
load only M3061 target tensor files listed in target_tensor_file_index_rows.csv
require every loaded observation_trace shape to be [T,72]
require target_action, target_action_mask, and target_loss_weight to be [T,3]
require finite tensors and action bounds inside [-1, 1]
require raw_action_trace_used_as_target false for every row
fail closed if any target tensor file is missing or malformed
```

M3065 split rules:

```text
use all 24 rows as public preflight accounting rows
create deterministic fit/internal-accounting split rows by measurement_episode_id
do not call the internal split validation, generalization, holdout, ranking, or promotion evidence
preserve binding_role, task_family, source_edge, and termination-reason coverage summaries
```

M3065 mask and weight rules:

```text
train only where target_action_mask > 0 and target_loss_weight > 0
use the three action dimensions independently, preserving [steer, throttle, brake]
record sample counts, mask counts, weight sums, and target_action_abs_max per row
fail closed if total masked steps, weight sum, or tensor shapes diverge from M3061 audit expectations
```

M3065 guard rules:

```text
offtrack_recovery numeric target tensors are the only positive direct-action fitting targets
candidate_binding_blocker remains a reporting gate, not a hidden actor input
collision_guard, success_preservation, and speed_floor remain guard/claim boundaries until closed-loop measurement
target_quality_validated remains false after fitting
closed-loop validation must wait for M3066 audit and a later measurement admission
```

## Actor And Side-Effect Boundaries

M3064 preserves the actor contract:

```text
actor observation shape: 72
actor action shape: 3
output semantics: direct_action
output components: steer;throttle;brake
base policy required at runtime: false
hidden oracle actor inputs: false
TTC actor input: false
target labels/provenance/source/route/outcome/progress/verdict actor-visible: false
checkpoint mutation in M3064: false
checkpoint mutation allowed in M3065: false
```

Any M3065 candidate artifact is an audit artifact only. It must stay separate
from parent checkpoints and cannot be promoted or deployed until a result audit
and later closed-loop measurement admit that route.

## Supported Claims

M3064 supports only:

```text
M3061/M3062 provide complete and claim-safe target tensor artifacts for 24 offtrack rows.
M3055 provides a direct obs72-to-action3 fitting contract with no runtime base policy dependency.
M3065 bounded direct-action fitting preflight is legally admissible.
M3065 is the only selected next route.
```

These are admission and route claims only.

## Rejected Claims

M3064 rejects:

```text
target quality validated: false
fitting executed in M3064: false
training executed in M3064: false
closed-loop validation/ranking/promotion executed: false
candidate selected or deployed: false
checkpoint mutated: false
repair success proved: false
driver performance improved: false
current-sim/high-fidelity/paper/full-driver/finite-window-vs-GRU/self-ID evidence produced: false
```

## Failure Taxonomy Summary

```text
contract_violation: not observed for M3061/M3062/M3055 actor contract artifacts; remains a hard fail for M3065.
lineage_invalid: not observed; M3065 lineage must point back to M3064, M3063, M3062, M3061, and M3055.
metric_artifact: active risk if M3065 fitting loss is interpreted as target quality or driver performance.
scenario_sampling_failure: unresolved because M3065 remains on the fixed 24-row offtrack denominator.
behavior_regression: unresolved until a later closed-loop measurement tests collision, offtrack, clearance, speed, and stability.
objective_overfit: active risk because fitting uses terminal offtrack public rows.
proof_washout: active risk if M3065 drops raw-action and target-provenance auditability.
seed_fragility: unresolved because no fresh distribution or private holdout is admitted here.
```

## Route Contract

M3064 selects exactly one next route:

```text
m3065-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-bounded-direct-action-fitting-preflight
```

M3065 must be an artifact-only offline fitting preflight. It must register
M3066 result audit and fail closed if the accepted target tensors cannot be
consumed without weakening loader, split, mask, weight, target-quality,
actor-input, checkpoint side-effect, or claim boundaries.

## Boundary

M3064 is a fitting-admission design milestone only. It opens one bounded direct
action fitting preflight because that is the next concrete step toward a
deployable active-safety reflex layer. It does not claim that the driver is
deployable, validated, robust, or complete.
