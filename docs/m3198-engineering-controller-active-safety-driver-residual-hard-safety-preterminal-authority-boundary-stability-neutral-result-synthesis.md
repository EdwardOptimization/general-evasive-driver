# M3198 Preterminal Authority Boundary-Stability Neutral Result Synthesis

## Summary

- status: completed
- decision: `pivot_to_m3199_candidate_vs_incumbent_residual_trace_delta_diagnostic`
- synthesis decision: pivot
- source audit: `docs/m3197-engineering-controller-active-safety-driver-residual-hard-safety-preterminal-authority-boundary-stability-candidate-full-fresh-measurement-result-audit.md`
- source measurement: `runs/m3196_engineering_controller_active_safety_driver_residual_hard_safety_preterminal_authority_boundary_stability_candidate_full_fresh_measurement_preflight/summary.json`
- incumbent preserved: M3105/M3103 deployable direct-action driver
- selected next route: `m3199-engineering-controller-active-safety-driver-residual-hard-safety-preterminal-authority-boundary-stability-neutral-candidate-vs-incumbent-trace-delta-diagnostic-materialization-preflight`

## Evidence Summary

The M3192-M3197 branch produced a complete but hard-safety-neutral candidate:

- M3192 admitted two actor-visible implementation families:
  `preterminal_clearance_authority_timing` and
  `boundary_stability_recovery_authority`.
- M3194 materialized a deterministic obs72-to-action3 candidate and kept
  `action_authority_saturation_guard` as a guard-only rule.
- M3196 measured the candidate on the complete 64-row fresh denominator.
- M3196 had 64 measurement rows, 0 failures, 128 same-row comparison rows, and
  exact seed matches against M3105 and M3181.
- Contract and claim gates passed.

The hard-safety counts are unchanged versus both M3105 and M3181:

- success count: 57
- collision count: 5
- offtrack count: 2
- speed-too-low count: 0
- success delta vs M3105: 0
- collision delta vs M3105: 0
- offtrack delta vs M3105: 0
- speed-too-low delta vs M3105: 0
- success delta vs M3181: 0
- collision delta vs M3181: 0
- offtrack delta vs M3181: 0
- speed-too-low delta vs M3181: 0

M3196 did show a small clearance-margin shift:

- clearance margin mean delta vs M3105: +0.03511151864840212
- clearance margin mean delta vs M3181: +0.014034883277526888

That shift is not enough to reduce terminal collision or offtrack outcomes.
It is measurement evidence, not validation, repair success, or a deployable
driver verdict.

## Supported Claims

- M3194 is a claim-safe deterministic obs72-to-action3 candidate artifact.
- M3196 is a complete same-denominator measurement artifact.
- The candidate preserves the actor-visible obs72 direct-action3 contract.
- M3105/M3103 remains the deployable incumbent.
- The M3194 candidate is hard-safety neutral versus M3105 and M3181 on the
  measured denominator.
- The candidate slightly shifts clearance margin without changing failure
  counts.

## Falsified Claims

- M3194/M3196 is not a hard-safety improvement over M3105.
- M3194/M3196 is not repair success.
- M3194/M3196 is not a validation result.
- M3194 is not a promotion candidate on M3196 evidence.
- Continuing direct candidate tuning without new step-level evidence is not
  justified.
- The residual blocker problem is not solved by the current preterminal
  authority and boundary-stability candidate.

## Failure Taxonomy Summary

- `behavior_regression`: not observed in hard-safety counts; the candidate is
  neutral versus M3105 and M3181.
- `objective_overfit`: risk is high if the branch tunes thresholds from the
  neutral full-fresh result without step-level causal evidence.
- `contract_violation`: not observed in M3194-M3197.
- `lineage_invalid`: avoided by preserving M3105/M3103 as incumbent.
- `metric_artifact`: not observed for M3196 row accounting; 64 rows, 128
  comparisons, and 0 measurement failures are present.
- `scenario_sampling_failure`: unresolved outside the current-sim denominator.
- `proof_washout`: high if neutral measurement is reworded as repair success or
  driver performance.
- `seed_fragility`: unresolved beyond the measured denominator.

## Public Gate Overfit Risk

The overfit risk is now high for direct implementation tuning. M3196 shows that
the candidate can shift actions enough to move clearance margin slightly, but
not enough to change the seven inherited blocker outcomes. A direct threshold
increase or stronger brake overlay would be a local guess unless we first
measure step-level candidate-vs-incumbent deltas on the residual blocker traces.

The next evidence should answer:

- whether the M3194 candidate engages before the terminal window on each
  residual failure row.
- whether engagement changes steering, throttle, or brake in the intended
  direction.
- whether action deltas are clipped, too late, too weak, or aimed at the wrong
  axis.
- whether offtrack rows need a different boundary-recovery signal than the one
  admitted in M3192.

## Next Branch Decision

Pivot to M3199 candidate-vs-incumbent residual trace-delta diagnostic
materialization:

- preserve M3105/M3103 as the deployable incumbent.
- execute or materialize the same seven residual blocker trace bindings for the
  M3194 candidate.
- compare M3194 trace-step actions and telemetry against the M3189 incumbent
  trace artifacts.
- classify per-row deltas by timing, sign, magnitude, clipping, and terminal
  outcome.
- keep the result diagnostic only.

M3199 must not implement new repair logic, mutate the public driver, run
validation, rank candidates, claim repair success, use hidden actor inputs, or
promote M3194. It should produce trace-delta diagnostic artifacts and an M3200
audit manifest.

## Claim Boundary

M3198 is synthesis and route selection only. It makes no implementation,
measurement result beyond interpreting M3196 as neutral, validation, ranking,
promotion, driver-performance, current-sim verdict, high-fidelity, full-driver,
repair-success, robustness-result, feasibility-proof, paper,
finite-window-vs-GRU, or self-ID claim.
