# M2890 Paper Route L0/L1/L2/L3 Capability-Prediction Modeling Contract Design

## Metadata

- status: completed
- decision: `admit_m2891_read_only_capability_prediction_modeling_contract_materialization_preflight`
- manifest: `experiments/manifests/m2890-paper-route-l0-l1-l2-l3-capability-prediction-modeling-contract-design.json`
- design artifact: `docs/m2890-paper-route-l0-l1-l2-l3-capability-prediction-modeling-contract-design.md`
- parent synthesis: `docs/m2889-paper-route-l0-l1-l2-l3-capability-prediction-materialization-audit-synthesis-or-modeling-design.md`
- parent audit: `docs/m2888-paper-route-l0-l1-l2-l3-capability-prediction-dataset-materialization-result-audit.md`
- parent summary: `runs/m2887_paper_route_l0_l1_l2_l3_capability_prediction_dataset_materialization_preflight/summary.json`
- parent profile-task rows: `runs/m2887_paper_route_l0_l1_l2_l3_capability_prediction_dataset_materialization_preflight/profile_task_rows.csv`
- parent evaluator targets: `runs/m2887_paper_route_l0_l1_l2_l3_capability_prediction_dataset_materialization_preflight/evaluator_target_rows.csv`
- parent actor contract: `runs/m2887_paper_route_l0_l1_l2_l3_capability_prediction_dataset_materialization_preflight/actor_feature_contract_rows.csv`
- follow-up manifest: `experiments/manifests/m2891-paper-route-l0-l1-l2-l3-capability-prediction-modeling-contract-materialization-preflight.json`
- next: `m2891-paper-route-l0-l1-l2-l3-capability-prediction-modeling-contract-materialization-preflight`

## Design Decision

M2890 selects exactly one next action:

```text
admit a read-only capability-prediction modeling-contract materialization
preflight
```

Formal decision:

```text
admit_m2891_read_only_capability_prediction_modeling_contract_materialization_preflight
```

M2890 does not admit model fitting yet. The accepted M2887/M2888/M2889 surface
has enough information to design a capability-prediction contract, but the
current artifacts are still contract rows rather than tensor-ready feature and
label arrays. M2891 must therefore materialize machine-checkable contract rows
for features, labels, splits, losses, metrics, baselines, and gates before any
model implementation or training can be considered.

## Evidence Summary

Accepted parent evidence:

```text
usable task rows: 17
profile-task rows: 204
required profiles: 12
L0 rows: 17
L1 rows: 17
L2 rows: 136
L3 rows: 34
evaluator-only target rows: 6
source-singleton exclusions: 34
guard exclusions: 21
actor observation dimension: 72
action dimension: 3
hidden/oracle actor input required: false
evaluator targets actor visible: false
```

The 12 controller-family profile names in the contract are:

```text
L0_current_masked
L1_one_step
L2_window_13
L2_window_13_current_tiled
L2_window_25
L2_window_25_current_tiled
L2_window_50
L2_window_50_current_tiled
L2_window_100
L2_window_100_current_tiled
L3_online_gru
L3_reset_control_corrected
```

The six evaluator-only target families are:

```text
future_braking_deceleration_envelope
future_yaw_authority
future_lateral_acceleration_response
actuator_response_lag_proxy
recovery_margin_after_maneuver
first_critical_action_quality
```

M2890 interprets this as an actor-safe modeling contract surface, not as
training evidence, ranking evidence, or paper proof.

## Actor-Safe Feature Contract

Allowed model inputs for later capability prediction must be deployable
controller observations only:

```text
ego kinematics
IMU-like response
steering/throttle/brake actuator state
previous physical commands
ego-frame road/free-space/obstacle geometry
past command-response history
finite-window history or recurrent hidden state when the profile admits it
```

M2891 must materialize feature contract rows with at least these fields:

```text
feature_contract_id
profile_name
profile_level
feature_family
feature_source
expected_shape
actor_visible_allowed
hidden_oracle_input_allowed
future_target_input_allowed
status_pass
failure_type
claim_boundary
```

Required feature families:

```text
current_deployable_observation
previous_command_and_actuator_state
finite_window_command_response_history
current_tiled_history_control
recurrent_hidden_state
```

The feature contract must distinguish profile capability from feature leakage:

```text
L0_current_masked:
  current deployable frame only.

L1_one_step:
  current deployable frame plus previous command and actuator state.

L2_window_*:
  explicit deployable command-response history windows.

L2_window_*_current_tiled:
  same model capacity with current frame repeated, used as a capacity/control
  baseline rather than history evidence.

L3_online_gru:
  deployable current frame plus online recurrent hidden state.

L3_reset_control_corrected:
  same recurrent architecture with reset/truncation control to test whether
  hidden state carries useful history.
```

Forbidden model inputs:

```text
mu
mass
center of gravity
tire stiffness
brake scale
actuator tau
slip ratio or slip angle
tire force or tire saturation
oracle feasibility
AEB/AES/drift labels
controller mode
speed_ref
beta_target
path error
heading error
path curvature
TTC
required clearance
oracle stopping distance
success/progress/route answers
future target values
```

Training-time diagnostics may record hidden or future quantities only in
evaluator-only label or audit fields. They must never be part of actor-visible
feature arrays.

## Evaluator-Only Label Contract

M2891 must materialize label contract rows from
`evaluator_target_rows.csv`. Required fields:

```text
label_contract_id
target_family
required_columns
available_columns
target_visibility
actor_visible_allowed
normalization_policy
missing_value_policy
loss_family
metric_family
status_pass
failure_type
claim_boundary
```

Target-level policies:

```text
future_braking_deceleration_envelope:
  regression over brake_scale, speed_mean, impact_speed_proxy, and
  delta_v_at_impact_mps. Use robust z-score normalization. Missing columns
  block implementation.

future_yaw_authority:
  regression over max_abs_yaw_rate, post_event_yaw_rate_abs, and beta_abs_peak.
  Use robust z-score normalization. Missing columns block implementation.

future_lateral_acceleration_response:
  regression over lateral_peak, lateral_rmse, and min_clearance_margin. Use
  robust z-score normalization and report tail-error metrics for
  min_clearance_margin.

actuator_response_lag_proxy:
  regression over previous_command_norm_mean, current_action_norm_mean, and
  action_trace_delta_mean. Use robust z-score normalization. This is an
  actuator-response target, not a hidden actuator-tau label.

recovery_margin_after_maneuver:
  mixed regression/classification over recovery_time_proxy,
  recoverability_window_success, and min_clearance_margin. The binary
  recoverability field uses BCE; continuous fields use robust regression.

first_critical_action_quality:
  mixed regression over first_obstacle_pass_step, plan_first_action_error_mean,
  and min_clearance_margin. This may be used for evaluator-side action-quality
  analysis only; it must not become an oracle controller answer.
```

Missing-value policy:

```text
missing required target column:
  fail the corresponding target contract row.

missing optional target value after required columns exist:
  materialize explicit availability mask and exclude that value from loss.

non-finite target value:
  fail the target row unless a documented mask marks it unavailable.
```

No label row may be actor visible.

## Split And Holdout Contract

The 17 usable rows are too small for a paper benchmark or controller-family
ranking. M2891 must therefore materialize split semantics but must not use the
split for fitting.

Minimum split contract:

```text
split_unit:
  task_source_id, not profile_task_id. Profiles for the same task_source_id
  must not leak across train/eval/holdout boundaries.

source groups:
  group by task_family, env_template_family, executable_source_family,
  source_edge, and diagnostic_artifact_tags.

public preflight split:
  allowed only for implementation smoke and schema checks.

paper holdout:
  not admitted by M2890. A future fresh/source-diverse panel must define it.

source-singleton rows:
  excluded from paper proof and ordinary success denominators. They may seed a
  later fresh panel design only.

guard rows:
  excluded from paper proof, ordinary success denominators, and training rows.
```

M2891 must report whether a non-leaking task-source split is possible for:

```text
T4 rows: 10
T5 rows: 7
t4_actuator_delay_response: 5
t4_capability_step_temporal: 3
t4_staged_warmup_capability: 2
t5_boundary_axis_retarget: 5
t5_near_boundary_warmup: 2
```

If any split would force a target family, task family, or source group into a
single split only, M2891 must mark the split as preflight-only and route to
fresh/source-diverse data design before paper evidence.

## Loss And Metric Contract

M2891 must materialize loss rows but must not run them.

Required loss families:

```text
robust_regression:
  Huber or smooth-L1 over normalized continuous target columns.

binary_recoverability:
  BCE over recoverability_window_success when available.

target_availability_mask:
  mask unavailable evaluator target values out of loss and metrics.

profile_pair_delta:
  optional future metric comparing prediction deltas between L0/L1/L2/L3
  profiles for the same task_source_id. M2891 may define it but must not
  compute paper claims.
```

Required metric families:

```text
per_target_mae
per_target_rmse
tail_error_for_margin_targets
calibration_error_by_target_family
profile_level_delta_summary
current_tiled_control_gap
reset_control_gap
leakage_guard_pass_rate
```

Metrics may support later implementation checks. They may not rank controllers
or establish finite-window-vs-GRU verdicts until a separate execution and audit
chain exists.

## Baseline Matrix Contract

The later modeling implementation must preserve this comparison matrix:

```text
L0-current:
  L0_current_masked

L1-one-step:
  L1_one_step

L2-finite-window:
  L2_window_13
  L2_window_25
  L2_window_50
  L2_window_100

L2-current-tiled-control:
  L2_window_13_current_tiled
  L2_window_25_current_tiled
  L2_window_50_current_tiled
  L2_window_100_current_tiled

L3-GRU:
  L3_online_gru

L3-reset-control:
  L3_reset_control_corrected
```

M2891 must fail if any required profile is missing from the 204 profile-task
matrix or if any profile has `training_scheduled`, `environment_rollout_scheduled`,
or `profile_specific_tuning` set true.

## Gate Contract

M2891 must write at least these gate rows:

```text
m2891-parent-summary-status-pass
m2891-profile-task-row-count
m2891-required-profile-coverage
m2891-actor-contract-preserved
m2891-evaluator-targets-actor-invisible
m2891-forbidden-feature-leakage-absent
m2891-label-contract-complete
m2891-split-contract-materialized
m2891-source-singleton-exclusions-preserved
m2891-guard-exclusions-preserved
m2891-no-implementation-or-training
m2891-follow-up-manifest-registered
```

Allowed failure types:

```text
lineage_invalid
contract_violation
metric_artifact
scenario_sampling_failure
objective_overfit
proof_washout
seed_fragility
```

## Follow-Up Decision

M2890 rejects immediate model implementation because feature and label
resolvability has not yet been materialized as machine-checkable rows.

M2890 rejects immediate fresh data design because a smaller read-only
contract-materialization preflight can first determine which fields and splits
are missing.

M2890 rejects Route A and Route C pivots because Route B has a concrete next
preflight and Route C/HF3 remains source-unavailable.

M2890 rejects stop because an actor-safe, evidence-producing follow-up exists.

The admitted follow-up is:

```text
m2891-paper-route-l0-l1-l2-l3-capability-prediction-modeling-contract-materialization-preflight
```

M2891 may write:

```text
summary.json
feature_contract_rows.csv
label_contract_rows.csv
split_contract_rows.csv
loss_metric_contract_rows.csv
baseline_contract_rows.csv
modeling_gate_rows.csv
claim_rows.csv
one bounded follow-up result-audit manifest
```

M2891 must not reset, step, roll out, replay, validate, fit a model, train,
rank, promote, publish a package, or claim driver performance,
finite-window-vs-GRU verdict, paper result, current-sim verdict,
high-fidelity validation, full-driver completion, or self-ID evidence.

## Supported Claims

M2890 supports only these claims:

```text
M2887/M2888/M2889 are sufficient to define an actor-safe capability-prediction
modeling contract.
The next route should be read-only contract materialization and resolvability
checking, not model fitting.
The current 17 usable rows remain preflight/design evidence only.
```

## Rejected Claims

M2890 rejects these interpretations:

```text
the contract proves driver performance: false
the contract ranks L0/L1/L2/L3 profiles: false
the contract proves finite-window-vs-GRU outcome: false
the contract proves current-response sufficiency: false
the contract proves recurrent self-ID: false
the contract admits actor-visible future targets: false
the contract admits hidden dynamics or oracle actor inputs: false
the contract admits training now: false
```

## Next Branch State

M2890 keeps the branch open as process/design progress:

```text
branch: paper_route_l0_l1_l2_l3_capability_prediction_modeling_contract
actual progress type: design_only
paper verdict delta: no verdict
local search risk: medium
```

The branch must synthesize or pivot if M2891 cannot materialize a complete
actor-safe contract, if it finds that the 17-row surface cannot support even
preflight split semantics, or if the next action would become another design
milestone without new materialized rows.
