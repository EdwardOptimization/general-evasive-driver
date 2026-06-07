# M2976 Engineering Controller Route A Actor-Head Delta Deployable Trace Capture Design

## Metadata

- status: completed
- decision: `admit_m2977_deployable_trace_capture_preflight`
- manifest: `experiments/manifests/m2976-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-deployable-trace-capture-design.json`
- parent synthesis: `docs/m2975-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-training-trace-branch-synthesis.md`
- parent audit: `docs/m2974-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-training-trace-panel-result-audit.md`
- parent trace panel: `runs/m2973_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_training_trace_panel_preflight/summary.json`
- follow-up manifest: `experiments/manifests/m2977-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-deployable-trace-capture-preflight.json`
- next: `m2977-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-deployable-trace-capture-preflight`

## Design Decision

M2976 admits one bounded deployable trace-capture preflight.

Formal decision:

```text
admit_m2977_deployable_trace_capture_preflight
```

The admitted route is a trace-capture/data preflight only. It may rerun the
accepted M2973/M2974 candidate and success-identity guard surface under the
read-only zero-residual actor-head delta wrapper only to persist raw deployable
observation/action/response traces. It is not residual fitting, not training,
not validation, not ranking, not winner selection, not checkpoint mutation, not
checkpoint promotion, and not a driver-performance, paper, current-sim,
high-fidelity, full-driver, finite-window-vs-GRU, or self-ID claim.

## Source Evidence

M2975 selects M2976 because M2973/M2974 preserve a complete metadata surface
but reject residual fitting readiness:

```text
training trace panel rows: 43
trace guard rows: 24
trace availability rows: 67
trace metadata present rows: 56
raw trace persisted rows: 0
trace panel ready for residual fitting: false
success identity guard rows: 13
stale guardrail rows: 11
actor observation/action: 72/action 3
```

The M2960 bounded execution rows show that the original diagnostic run recorded
per-row rollout metadata such as step count, outcome, termination, checkpoint,
profile, actor-head delta identity mode, and claim boundaries. They do not
persist raw deployable trace tensors.

## M2977 Capture Contract

M2977 must produce a raw deployable trace dataset with this contract:

```text
capture source:
  M2973 trace_panel_rows.csv
  M2973 trace_guard_rows.csv
  M2973 trace_availability_rows.csv
  M2960 bounded_execution_rows.csv

executed capture rows:
  43 future training candidate rows
  13 success identity guard rows

non-executed protected rows:
  11 stale fixed-source guardrails

actor-visible tensors per executed row:
  observation_trace: float32 [T, 72]
  action_trace: float32 [T, 3]
  next_observation_trace: float32 [T, 72]
  reward_trace: float32 [T]
  done_trace: bool [T]
  timeout_trace: bool [T]

metadata per executed row:
  execution_candidate_id
  training_admission_candidate_id or guard row id
  workload_id
  task_family
  objective_or_guard_family
  outcome_family
  source_milestone
  parent_checkpoint_path
  parent_profile_config_path
  eval_seed
  trace_step_count
  zero_residual_identity_mode
  residual_delta_abs_max
  termination_reason
  completion_reason
```

The raw trace tensors must be deployable actor-view traces. They must not
include hidden dynamics, oracle state, future targets, objective labels,
admission labels, trace-readiness labels, success/progress labels, verdict
labels, source-family labels, route labels, or paper/validation denominators as
actor input.

## Required Artifacts

M2977 must write:

```text
runs/m2977_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_deployable_trace_capture_preflight/summary.json
runs/m2977_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_deployable_trace_capture_preflight/capture_plan_rows.csv
runs/m2977_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_deployable_trace_capture_preflight/raw_trace_index_rows.csv
runs/m2977_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_deployable_trace_capture_preflight/raw_trace_guard_rows.csv
runs/m2977_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_deployable_trace_capture_preflight/raw_trace_availability_rows.csv
runs/m2977_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_deployable_trace_capture_preflight/actor_contract_guard_rows.csv
runs/m2977_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_deployable_trace_capture_preflight/claim_boundary_rows.csv
runs/m2977_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_deployable_trace_capture_preflight/gate_matrix.csv
runs/m2977_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_deployable_trace_capture_preflight/raw_traces/*.npz
docs/m2977-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-deployable-trace-capture-preflight.md
```

The `raw_trace_index_rows.csv` file must map each executed row to a raw trace
file and record tensor shapes. The `raw_trace_guard_rows.csv` file must preserve
the 13 success identity guards and 11 stale fixed-source guardrails separately.
The stale guardrails must remain non-executed protected rows.

## Gates

M2977 must pass these gates:

```text
required artifacts present: true
raw trace files exist for executed rows: true
executed raw trace row count: 56
future training candidate raw traces: 43
success identity raw traces: 13
stale fixed-source guardrails executed: 0
stale fixed-source guardrails preserved: 11
actor observation dim: 72
actor action dim: 3
observation/action/next_observation tensors finite: true
hidden/oracle/future-target actor input detected: false
objective/admission/trace-readiness/verdict labels actor-visible: false
checkpoint loaded read-only: true
checkpoint mutation/saving/promotion: false
residual fitting/training/PPO/validation/ranking/winner selection: false
repair-success/performance/paper/current-sim/high-fidelity/full-driver/finite-window-vs-GRU/self-ID claims: false
```

If M2977 cannot persist raw deployable traces for all 56 executed candidate and
success-identity rows, it must fail closed and route to an audit or repair
decision. It must not silently downgrade to metadata-only traces.

## Boundary

M2976 does not run M2977. It only defines the route and required contract. The
next milestone must implement the smallest capture preflight that can test the
raw trace persistence hypothesis while preserving actor and claim boundaries.
