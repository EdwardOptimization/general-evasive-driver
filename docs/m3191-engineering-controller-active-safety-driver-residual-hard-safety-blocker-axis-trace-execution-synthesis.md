# M3191 Residual Hard-Safety Blocker Axis Trace Execution Synthesis

## Summary

- status: completed
- decision: `continue_to_m3192_preterminal_authority_boundary_stability_admission_materialization`
- synthesis decision: continue
- source audit: `docs/m3190-engineering-controller-active-safety-driver-residual-hard-safety-blocker-axis-trace-execution-result-audit.md`
- source telemetry: `runs/m3189_engineering_controller_active_safety_driver_residual_hard_safety_blocker_axis_trace_execution_materialization_preflight/summary.json`
- incumbent preserved: M3105/M3103 deployable direct-action driver
- selected next route: `m3192-engineering-controller-active-safety-driver-residual-hard-safety-preterminal-authority-boundary-stability-admission-materialization-preflight`

## Evidence Summary

M3189 executed the seven accepted residual blocker trace bindings through the
incumbent `ActiveSafetyReflexDriver.act(obs72)` runtime:

- trace execution rows: 7
- trace step rows: 255
- trace failures: 0
- hidden actor inputs used: false
- public driver default mutated: false
- runtime base policy required: false

The executed residual outcomes remain:

- success rows: 0
- collision rows: 5
- offtrack rows: 2
- speed-too-low rows: 0

This is residual blocker telemetry, not validation or repair-success evidence.

The terminal-window evidence is structured enough to select a next admission
axis:

- Collision rows remain high-speed at terminal, with last-step speeds from
  14.164 to 18.750 m/s and terminal clearance margins from -0.112 to -0.231.
- Collision rows show late or saturated authority: terminal-window clip steps
  are 3/5, 5/5, 5/5, 5/5, and 5/5 across the five collision blockers.
- Boundary-recovery collision rows have terminal-window clip steps of 5/5 on
  all three rows, which points to late action authority rather than absent
  action output.
- Offtrack rows have terminal-window lateral-error means around 4.7 to 4.8 and
  terminal lateral errors around 5.0. Their terminal-window sideslip absolute
  means are about 0.46 and 0.69.
- One offtrack row has no action clipping, while the other clips in the final
  five steps. This rejects a pure saturation-only explanation for offtrack.

The trace therefore supports a bounded implementation-admission route around
pre-terminal timing and boundary-stability gating, not another local steer-delta
or terminal-only action-delta route.

## Supported Claims

- M3189 provides complete trace telemetry for the seven residual blocker rows.
- The actor contract remains obs72-only direct action3.
- The residual blockers split into collision-clearance timing, boundary-
  recovery collision, and boundary-recovery stability failure surfaces.
- A pure terminal action-authority explanation is insufficient: collision rows
  are often saturated at terminal, while one offtrack row is not clipped.
- A next admission materialization can be defined around actor-visible pre-
  terminal clearance timing and boundary-stability signals.

## Falsified Claims

- M3189 is not validation.
- M3189 is not repair success.
- M3189 is not driver-performance or current-sim verdict evidence.
- Pure steer-delta continuation is not justified by the seven-row telemetry.
- Pure action saturation alone is not sufficient to explain the two offtrack
  blockers.
- Implementation is not yet admitted until admission rows and guards are
  materialized and audited.

## Failure Taxonomy Summary

- `behavior_regression`: not newly measured in M3191; M3105 remains incumbent.
- `objective_overfit`: risk is high if the next route targets only terminal
  action saturation and ignores offtrack stability.
- `contract_violation`: not observed in M3189.
- `lineage_invalid`: avoided by preserving M3105/M3103 as incumbent.
- `metric_artifact`: not observed for M3189 row accounting; 7 execution rows,
  255 step rows, and 0 failure rows are present.
- `scenario_sampling_failure`: unresolved outside the selected seven residual
  blocker rows.
- `proof_washout`: high if the trace rows are reworded as validation,
  performance, or repair-success evidence.
- `seed_fragility`: unresolved beyond these same-case residual rows.

## Public Gate Overfit Risk

The overfit risk is high if the next branch directly codes a rule from terminal
failures. M3189 shows terminal symptoms, but implementation must be admitted
only if the rule can be expressed from actor-visible obs72 signals before the
terminal step and can be guarded against public-driver mutation and hidden-label
inputs.

The safer route is an admission materialization that binds each candidate rule
family to:

- allowed actor-visible obs72 proxies,
- forbidden hidden labels and TTC,
- targeted blocker family,
- expected action-channel effect,
- measurable future proof gate,
- and explicit stop conditions.

## Next Branch Decision

Continue to M3192 pre-terminal authority and boundary-stability admission
materialization:

- preserve M3105/M3103 as the deployable incumbent.
- materialize implementation-admission rows for two bounded actor-visible rule
  families:
  - `preterminal_clearance_authority_timing`: earlier collision-clearance
    intervention before terminal saturation.
  - `boundary_stability_recovery_authority`: boundary recovery and sideslip
    damping for offtrack rows.
- keep `action_authority_saturation` as a cross-cutting guard and diagnostic,
  not a standalone implementation thesis.
- reject direct implementation until M3192 admission artifacts pass and M3193
  audits them.

M3192 must not execute env steps, implement repair logic, mutate the public
driver, run validation, rank candidates, claim repair success, or use hidden
actor inputs. It should produce admission rows, rule-contract rows, forbidden-
label guard rows, gate rows, a doc, and an M3193 result-audit manifest.

## Claim Boundary

M3191 is synthesis and route selection only. It makes no repair implementation,
measurement, validation, ranking, promotion, driver-performance, current-sim
verdict, high-fidelity, full-driver, repair-success, robustness-result,
feasibility-proof, paper, finite-window-vs-GRU, or self-ID claim.
