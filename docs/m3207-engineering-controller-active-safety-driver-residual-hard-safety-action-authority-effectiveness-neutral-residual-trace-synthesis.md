# M3207 Action-Authority/Effectiveness Neutral Residual-Trace Synthesis

## Summary

- status: completed
- decision: `pivot_to_recovery_clearance_supervisor_architecture_materialization`
- synthesis decision: pivot
- source audit: `docs/m3206-engineering-controller-active-safety-driver-residual-hard-safety-action-authority-effectiveness-candidate-residual-trace-measurement-result-audit.md`
- source measurement: `runs/m3205_engineering_controller_active_safety_driver_residual_hard_safety_action_authority_effectiveness_candidate_residual_trace_measurement_preflight/summary.json`
- incumbent preserved: M3105/M3103 deployable direct-action driver
- selected next route: `m3208-engineering-controller-active-safety-driver-residual-hard-safety-recovery-clearance-supervisor-architecture-materialization-preflight`

## Evidence Summary

The M3199-M3206 action-authority/effectiveness branch answered a narrow
question: whether stronger local direct-action authority on the residual
blocker traces is enough to change terminal hard-safety outcomes.

The answer is no on the measured residual trace set:

- M3199 showed nonzero candidate-vs-incumbent action deltas but no outcome
  changes on the same seven residual blocker traces.
- M3201/M3202 admitted three actor-visible action-authority/effectiveness rule
  families and one guard-only saturation family.
- M3203 materialized a stronger deterministic obs72-to-action3 candidate while
  preserving the public driver default.
- M3205 executed that candidate on the same seven residual traces with 0
  execution failures and preserved the obs72-only direct-action contract.
- M3205 outcome counts remained 0 success, 5 collision, and 2 offtrack, exactly
  matching M3194 and the incumbent on those traces.
- M3206 accepted M3205 as complete and claim-safe, but behavior-neutral.

This means the branch produced useful negative evidence. It shows that
stronger local steering/brake/throttle authority, applied as a scalar rule
extension of the incumbent family, is not enough to resolve the residual
collision and offtrack blockers.

## Supported Claims

- The action-authority/effectiveness route is complete enough to interpret as
  behavior-neutral on the accepted residual trace set.
- The M3203 candidate changed actions without changing terminal outcomes.
- M3105/M3103 remains the deployable incumbent.
- The next engineering route should change architecture and evidence axis, not
  continue local threshold amplification.
- The actor runtime boundary remains obs72-only direct action3.

## Falsified Claims

- Local action-strength amplification is sufficient to fix the residual
  collision/offtrack blockers.
- M3203/M3205 is repair success.
- M3203/M3205 admits validation, ranking, promotion, or public driver mutation.
- A full-fresh run of M3203 is justified by residual trace evidence.
- The residual blocker problem is solved by action magnitude or terminal-window
  authority alone.

## Failure Taxonomy Summary

- `behavior_regression`: not observed in M3205 terminal counts, but no
  improvement is observed either.
- `objective_overfit`: high if the project keeps tuning scalar thresholds on
  the same seven residual traces.
- `contract_violation`: not observed across M3201-M3206.
- `lineage_invalid`: avoided by preserving M3105/M3103 as incumbent and
  routing interpretation through M3206.
- `metric_artifact`: not observed for M3205 row accounting or guards.
- `scenario_sampling_failure`: unresolved outside the selected residual traces.
- `proof_washout`: high if clearance-margin deltas are elevated above terminal
  collision/offtrack outcomes.
- `seed_fragility`: unresolved outside the residual trace set and current-sim
  denominator.

## Public Gate Overfit Risk

The overfit risk is high for another local repair attempt. The branch has now
materialized probes, admission rows, candidate implementation, same-trace
diagnostics, and same-trace closed-loop measurement. The action changed, but
the safety outcomes did not. Continuing by increasing the same thresholds would
likely optimize implementation probes rather than the collision, clearance,
stability, recovery, and robustness objective.

The route should pivot to an architecture that explicitly budgets clearance and
recovery over modes, rather than treating residual failures as isolated action
delta shortages.

## Next Branch Decision

Pivot to M3208 recovery-clearance supervisor architecture materialization:

- use a new workflow branch:
  `active_safety_driver_residual_hard_safety_recovery_clearance_supervisor`.
- preserve the runtime contract:
  `obs72 -> direct [steer, throttle, brake]`.
- preserve M3105/M3103 as the deployable incumbent until measured evidence
  supports replacement.
- materialize an architecture-level candidate artifact with explicit mode
  hierarchy, action budget, clearance objective, boundary recovery objective,
  speed management, and bounded fallback behavior.
- require actor-visible feature extraction only; forbid source labels, row
  outcomes, baseline outcomes, TTC oracle, route/progress/verdict labels, and
  future terminal status as runtime inputs.
- keep M3208 as materialization only; no validation, ranking, promotion, public
  driver default mutation, repair-success, current-sim verdict, high-fidelity,
  paper, finite-window-vs-GRU, or self-ID claim.

M3208 should produce a runnable materialization route and a follow-up audit
manifest before any measurement. The next measured question should be whether a
mode-level recovery/clearance supervisor changes the same residual terminal
outcomes, not whether another scalar threshold is larger than M3203.

## Claim Boundary

M3207 is synthesis and route selection only. It makes no implementation,
measurement beyond interpreting M3205 as behavior-neutral, validation, ranking,
promotion, driver-performance, current-sim verdict, high-fidelity, full-driver,
repair-success, robustness-result, feasibility-proof, paper,
finite-window-vs-GRU, or self-ID claim.
