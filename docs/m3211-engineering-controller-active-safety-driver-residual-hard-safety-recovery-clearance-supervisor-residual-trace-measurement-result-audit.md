# M3211 Recovery-Clearance Supervisor Residual-Trace Measurement Result Audit

## Summary

- status: completed
- decision: `accept_m3210_claim_safe_behavior_neutral_route_to_m3212_synthesis`
- result class: `accepted_complete_claim_safe_behavior_neutral`
- source summary: `runs/m3210_engineering_controller_active_safety_driver_residual_hard_safety_recovery_clearance_supervisor_residual_trace_measurement_preflight/summary.json`
- M3210 status pass: true
- M3210 gate matrix pass: true
- selected next route: `m3212-engineering-controller-active-safety-driver-residual-hard-safety-recovery-clearance-supervisor-neutral-residual-trace-synthesis`

## Artifact Audit

M3210 is accepted as complete and claim-safe:

- scheduled trace bindings: 7
- candidate trace execution rows: 7
- candidate trace step rows: 256
- trace execution failures: 0
- same-trace comparison rows: 7
- contract guard rows: present and passing
- claim-boundary rows: present and passing
- gate matrix: passing
- follow-up manifest registered: true

The runtime contract is preserved:

```text
input: actor-visible obs72 only
output: direct clipped action3 [steer, throttle, brake]
runtime_base_policy_required: false
checkpoint_model_required: false
hidden/runtime oracle labels: not used
public driver default mutated: false
```

## Measurement Audit

M3210 executed the M3208 deterministic recovery-clearance supervisor candidate
on the same seven residual blocker trace bindings and compared same-trace
outcomes against M3205, M3199/M3194, and M3189 incumbent artifacts.

The terminal hard-safety counts are unchanged:

- M3210 success/collision/offtrack: 0/5/2
- M3205 success/collision/offtrack: 0/5/2
- M3194 success/collision/offtrack: 0/5/2
- incumbent success/collision/offtrack: 0/5/2
- outcome changed versus M3205/M3194/incumbent: 0/0/0
- hard-safety improved versus M3205/M3194/incumbent: 0/0/0
- hard-safety regressed versus M3205/M3194/incumbent: 0/0/0

M3210 does change actions materially versus M3205: 255 meaningful action-delta
steps across the seven aligned traces, with 220 preterminal deltas and a mean
per-trace action-delta L2 of about 0.507. That did not change any terminal
collision or offtrack outcome. Clearance margins improved slightly on five
rows, but the two clearance-timing rows regressed in margin, and all seven
terminal outcomes stayed failed.

This makes M3210 behavior-neutral on the residual hard-safety blocker set, not
repair success.

## Supported Claims

- M3210 produced complete same-seven residual-trace measurement artifacts for
  the M3208 recovery-clearance supervisor candidate.
- The M3208 candidate can run as a full obs72-to-action3 action source on the
  accepted trace bindings without execution failures.
- The direct-action actor contract remains obs72-only with `[steer, throttle,
  brake]` output.
- The supervisor branch changed actions but did not change the seven residual
  terminal outcomes.
- M3105/M3103 remains the deployable incumbent.

## Rejected Claims

- M3210 is not validation.
- M3210 is not ranking, winner selection, checkpoint mutation, promotion, or
  public driver default replacement.
- M3210 is not driver-performance, current-sim verdict, robustness-result,
  high-fidelity, paper, finite-window-vs-GRU, full-driver, repair-success,
  feasibility-proof, or self-ID evidence.
- M3210 does not admit full-fresh measurement, because the residual-trace
  blocker set shows no hard-safety improvement versus M3205, M3194, or
  incumbent evidence.
- Mode-level recovery/clearance supervision is not sufficient evidence for
  deployment on this branch.

## Failure Taxonomy

- `contract_violation`: not observed; obs72/action3/direct-action and hidden
  input guards pass.
- `lineage_invalid`: not observed; M3210 follows accepted M3209/M3208 and
  compares the same trace bindings against M3205, M3199/M3194, and M3189.
- `metric_artifact`: not observed; row counts, guards, gate matrix, summary,
  and documentation are present.
- `scenario_sampling_failure`: unresolved beyond the same seven residual
  blocker traces; M3210 is not a broad denominator.
- `behavior_regression`: not observed in terminal hard-safety counts, although
  clearance margin regressed on two clearance-timing rows.
- `objective_overfit`: active risk if the project keeps tuning mode budgets on
  the same seven traces despite unchanged terminal outcomes.
- `proof_washout`: active risk if action deltas or small clearance shifts are
  reworded as repair success while collisions and offtrack terminations remain
  unchanged.
- `seed_fragility`: unresolved outside the fixed residual trace set.

## Public Gate Overfit Risk

Risk is high for continuing this local branch as another threshold or budget
tuning loop. M3205 already showed action changes with no outcome change. M3210
changes nearly every aligned action step relative to M3205, yet the residual
terminal outcomes remain 0 success, 5 collisions, and 2 offtrack.

The next route should synthesize the branch and decide whether to pivot to a
different evidence axis. Full-fresh validation and deployable-driver mutation
are not admitted by this evidence.

## Next Branch Decision

Route exactly one follow-up to:

```text
m3212-engineering-controller-active-safety-driver-residual-hard-safety-recovery-clearance-supervisor-neutral-residual-trace-synthesis
```

M3212 should close or pivot the recovery-clearance supervisor branch. It must
preserve M3105/M3103 as incumbent, reject full-fresh validation on M3210
evidence, and select a new route only if it changes the evidence axis beyond
local mode-budget tuning on the same residual trace set.

## Claim Boundary

M3211 is a result audit only. It runs no reset, step, rollout, replay, fitting,
PPO, training, validation, ranking, promotion, high-fidelity simulation,
finite-window-vs-GRU comparison, or self-ID test.
