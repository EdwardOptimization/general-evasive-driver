# M3212 Recovery-Clearance Supervisor Neutral Residual-Trace Synthesis

## Summary

- status: completed
- decision: `pivot_to_terminal_cause_action_effect_decomposition_route_plan`
- synthesis decision: pivot
- source audit: `docs/m3211-engineering-controller-active-safety-driver-residual-hard-safety-recovery-clearance-supervisor-residual-trace-measurement-result-audit.md`
- source measurement: `runs/m3210_engineering_controller_active_safety_driver_residual_hard_safety_recovery_clearance_supervisor_residual_trace_measurement_preflight/summary.json`
- incumbent preserved: M3105/M3103 deployable direct-action driver
- selected next route: `m3213-engineering-controller-active-safety-driver-residual-hard-safety-terminal-cause-action-effect-decomposition-route-plan`

## Evidence Summary

The M3208-M3211 recovery-clearance supervisor branch answered a narrow
question: whether a mode-level clearance, boundary, stability, speed, and
fallback supervisor changes the same residual collision/offtrack outcomes that
survived M3205.

The answer is no on the measured residual trace set:

- M3208 materialized a deterministic obs72-to-action3 supervisor with fallback,
  collision, boundary, and stability modes.
- M3209 accepted the architecture artifacts as complete and claim-safe, but not
  as measurement, validation, or repair success.
- M3210 executed the M3208 candidate on the same seven residual trace bindings
  with 0 execution failures and preserved the obs72-only direct-action
  contract.
- M3210 changed actions materially versus M3205: 255 meaningful action-delta
  steps, including 220 preterminal deltas.
- M3210 terminal counts remained 0 success, 5 collision, and 2 offtrack,
  exactly matching M3205, M3194, and incumbent evidence.
- M3211 accepted M3210 as complete and claim-safe, but behavior-neutral.

This is useful negative evidence. It shows that the current mode-budget
supervisor changes control outputs but does not change the residual terminal
causes. The next route should not keep increasing local steering, throttle, or
brake budgets on the same traces.

## Supported Claims

- The recovery-clearance supervisor route is complete enough to interpret as
  behavior-neutral on the accepted residual trace set.
- The M3208 candidate changed actions without changing terminal outcomes.
- M3105/M3103 remains the deployable incumbent.
- The next engineering route should change evidence axis from action-budget
  design to terminal-cause/action-effect decomposition.
- The actor runtime boundary remains obs72-only direct action3.

## Falsified Claims

- Mode-level clearance/boundary/stability budget supervision is sufficient to
  fix the residual collision/offtrack blockers.
- M3208/M3210 is repair success.
- M3208/M3210 admits validation, ranking, promotion, or public driver mutation.
- A full-fresh run of M3208 is justified by residual trace evidence.
- The residual blocker problem is solved by changing direct-action magnitudes
  alone.

## Failure Taxonomy Summary

- `behavior_regression`: not observed in terminal counts, but clearance margin
  regressed on two clearance-timing rows.
- `objective_overfit`: high if the project keeps tuning supervisor mode
  budgets on the same seven residual traces.
- `contract_violation`: not observed across M3208-M3211.
- `lineage_invalid`: avoided by preserving M3105/M3103 as incumbent and
  routing interpretation through M3211.
- `metric_artifact`: not observed for M3210 row accounting or guards.
- `scenario_sampling_failure`: unresolved outside the selected residual traces.
- `proof_washout`: high if action deltas or small clearance-margin shifts are
  elevated above terminal collision/offtrack outcomes.
- `seed_fragility`: unresolved outside the residual trace set and current-sim
  denominator.

## Public Gate Overfit Risk

The overfit risk is high for another local repair attempt. Two consecutive
branches now changed action telemetry without changing residual terminal
outcomes:

- M3205 changed action behavior versus M3194/incumbent but remained 0/5/2.
- M3210 changed action behavior versus M3205/M3194/incumbent but remained
  0/5/2.

Continuing direct-action budget tuning would likely optimize local artifacts
instead of explaining why collisions and offtrack terminations remain
unavoidable or uncorrected in the terminal windows.

## Next Branch Decision

Pivot to M3213 terminal-cause/action-effect decomposition route planning:

- use a new workflow branch:
  `active_safety_driver_residual_hard_safety_terminal_cause_action_effect_decomposition`.
- preserve the runtime contract:
  `obs72 -> direct [steer, throttle, brake]`.
- preserve M3105/M3103 as the deployable incumbent until measured evidence
  supports replacement.
- perform no new rollout in the route-plan milestone.
- use existing M3210, M3205, M3199, and M3189 trace-step artifacts to define an
  offline decomposition that can classify each residual trace into actor-visible
  failure hypotheses such as late intervention, wrong-direction action,
  insufficient speed envelope, unrecoverable geometry by the observed window,
  boundary corridor loss, or action-effect latency.
- explicitly separate offline diagnostic labels from future actor runtime
  inputs.
- require the next executable diagnostic to prove whether an actor-visible
  feature/action pathway exists before any new repair implementation,
  full-fresh measurement, validation, ranking, promotion, public driver default
  mutation, repair-success, current-sim verdict, robustness-result,
  high-fidelity, paper, finite-window-vs-GRU, feasibility-proof, or self-ID
  claim.

M3213 should produce a route document and a bounded follow-up manifest for
terminal-cause/action-effect decomposition. It should not implement a new
driver yet.

## Claim Boundary

M3212 is synthesis and route selection only. It makes no implementation,
measurement beyond interpreting M3210 as behavior-neutral, validation, ranking,
promotion, driver-performance, current-sim verdict, high-fidelity, full-driver,
repair-success, robustness-result, feasibility-proof, paper,
finite-window-vs-GRU, or self-ID claim.
