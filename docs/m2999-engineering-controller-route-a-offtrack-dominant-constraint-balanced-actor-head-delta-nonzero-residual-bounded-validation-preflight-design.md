# M2999 Engineering Controller Route A Actor-Head Delta Nonzero Residual Bounded Validation Preflight Design

## Metadata

- status: completed
- decision: `admit_m3000_bounded_diagnostic_validation_preflight`
- manifest: `experiments/manifests/m2999-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-bounded-validation-preflight-design.json`
- parent synthesis: `docs/m2998-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-validation-contract-branch-synthesis.md`
- parent contract summary: `runs/m2996_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_success_identity_guard_constrained_fitting_validation_contract_materialization_preflight/summary.json`
- follow-up manifest: `experiments/manifests/m3000-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-bounded-diagnostic-validation-preflight.json`
- next: `m3000-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-bounded-diagnostic-validation-preflight`

## Design Premise

M2999 is the final design-only gate admitted by M2998. It does not run reset,
step, rollout, validation, ranking, winner selection, promotion, private
holdout, performance measurement, training, or checkpoint mutation.

The M2998 synthesis allowed exactly one design step because M2993-M2997
materialized a claim-safe residual-head artifact and validation-contract
surface, but no closed-loop validation data. M2999 therefore either had to
admit a data-producing diagnostic preflight, identify a concrete contract
repair, pivot to Route C/interface work, or stop.

The decision is to admit M3000 as a bounded diagnostic validation preflight.
This is allowed because the M2996 contracts already define the wrapper,
candidate denominator, success-retention denominator, stale fixed-source
exclusions, parent-comparison plan, actor-input exclusions, side-effect guards,
claim boundaries, and gate matrix needed before execution.

## Input Surface

M3000 may consume only the audited M2996/M2998 surface:

```text
M2998 synthesis doc:
  docs/m2998-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-validation-contract-branch-synthesis.md

M2996 validation-contract directory:
  runs/m2996_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_success_identity_guard_constrained_fitting_validation_contract_materialization_preflight

M2996 required rows:
  validation_contract_rows.csv
  residual_head_wrapper_contract_rows.csv
  parent_comparison_plan_rows.csv
  success_behavior_retention_guard_rows.csv
  stale_exclusion_guard_rows.csv
  actor_input_exclusion_rows.csv
  checkpoint_side_effect_guard_rows.csv
  claim_boundary_rows.csv
  gate_matrix.csv

M2993 residual-head artifact:
  runs/m2993_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_success_identity_guard_constrained_fitting_preflight/candidate_residual_head_artifact.npz
```

The M3000 input denominator is fixed:

```text
candidate validation rows: 43
success-retention rows: 13
stale fixed-source exclusions: 11
actor observation/action: 72/3
residual artifact shape: 72 x 3 / action 3
residual limit: 0.07999999821186066
success-retention residual abs max before execution: 0.00034158502239733934
```

M3000 must reject any row that lacks a raw trace path, target tensor path,
candidate wrapper plan, parent-comparison plan, or claim-safe status.

## Wrapper And Execution Boundary

M3000 must load the parent checkpoint and candidate residual-head artifact
read-only. It may instantiate a residual actor-head delta wrapper, but it must
not mutate, save, rank, select, or promote either parent checkpoint or
candidate artifact.

The wrapper rule is:

```text
parent action = parent actor(observation)
candidate residual = clip(linear_residual_head(observation), residual_limit)
candidate action = clamp(parent action + candidate residual, action bounds)
```

The residual head must receive only the deployed actor observation vector. It
must not receive target labels, target provenance, objective/admission/source
labels, route decisions, audit verdicts, paper labels, hidden parameters,
oracle feasibility, TTC, required clearance, path-error labels, or success
progress labels.

The current M2960/M2977 actor-head delta execution and trace-capture path is
the implementation precedent. M3000 should reuse that read-only execution
pattern, but replace zero-residual identity mode with the M2993 read-only
candidate residual-head wrapper.

## Diagnostic Validation Protocol

M3000 may execute one bounded diagnostic rollout per admitted M2996 validation
contract row, with matching parent/candidate accounting. The comparison is
report-only.

Required row accounting:

```text
candidate_validation_execution_rows:
  one row per admitted M2996 validation contract, or a failure row explaining
  why that row could not execute without boundary changes

parent_comparison_report_rows:
  parent and candidate diagnostics over the fixed denominator only
  no ranking, no winner, no promotion, no success-rate verdict

success_behavior_retention_rows:
  one row per M2996 success-retention guard
  checks whether the candidate wrapper preserves already-successful traces
  records behavior-regression risk without treating retention as repair success

stale_exclusion_guard_rows:
  11 stale fixed-source rows carried as excluded guardrails
  not executed, not counted in validation/paper/self-ID denominators

side_effect_guard_rows:
  parent checkpoint read-only
  residual-head artifact read-only
  checkpoint save/mutation/promotion false
```

M3000 may record diagnostic metrics such as termination reason, collision,
offtrack, obstacle completion, minimum clearance, episode length, return,
residual abs max, residual trace count, and finite metric checks. These are
diagnostic fields only.

## Output Artifacts

M3000 should write:

```text
runs/m3000_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_bounded_diagnostic_validation_preflight/summary.json
candidate_validation_execution_rows.csv
candidate_validation_failure_rows.csv
parent_comparison_report_rows.csv
success_behavior_retention_execution_rows.csv
stale_exclusion_guard_rows.csv
actor_input_guard_rows.csv
checkpoint_side_effect_guard_rows.csv
claim_boundary_rows.csv
gate_matrix.csv
run_state.json
docs/m3000-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-bounded-diagnostic-validation-preflight.md
experiments/manifests/m3001-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-bounded-diagnostic-validation-result-audit.json
```

M3000 should fail closed if it cannot write complete artifacts. A failed
M3000 can still be useful evidence if it preserves failure rows and routes to
M3001 result audit.

## Gate Matrix

M3000 passes as a diagnostic preflight only if all of these hold:

```text
M2996 summary status_pass true and gate_matrix_pass true
43 candidate validation rows loaded
13 success-retention rows loaded
11 stale exclusion rows loaded
all candidate rows executed or explicitly accounted by failure rows
stale rows executed false
stale rows in validation/paper/self-ID denominators false
parent comparison report-only true
ranking run false
winner selected false
promotion run false
checkpoint mutated false
parent checkpoint read-only true
candidate residual-head artifact read-only true
actor observation/action 72/3 preserved
target labels/provenance/objective/source/route/verdict/paper labels actor-visible false
hidden/oracle actor input required false
success-rate verdict claim made false
repair-success claim made false
driver-performance claim made false
paper/current-sim/high-fidelity/full-driver/FW-vs-GRU/self-ID claim made false
M3001 result-audit manifest registered before interpretation
```

## Rejected Routes

M2999 rejects:

```text
direct ranking or promotion of the M2993 residual-head artifact
private holdout execution
paper or self-ID interpretation from current-sim diagnostic rows
another static materialization/audit/design loop before data
including stale fixed-source rows in validation, paper, or self-ID denominators
turning parent comparison into a winner selection
weakening actor input boundaries to make validation easier
```

## Next Route

Decision:

```text
admit_m3000_bounded_diagnostic_validation_preflight
```

M3000 must produce new closed-loop diagnostic data or explicit failure rows
while preserving all actor, stale-exclusion, parent-comparison, checkpoint,
side-effect, and claim boundaries. The result must be audited by M3001 before
any interpretation.
