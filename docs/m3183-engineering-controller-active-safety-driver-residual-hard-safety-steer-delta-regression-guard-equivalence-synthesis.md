# M3183 Steer-Delta Regression Guard Equivalence Synthesis

## Summary

- status: completed
- decision: `pivot_to_m3184_residual_hard_safety_blocker_axis_expansion_plan`
- synthesis decision: pivot
- source audit: `docs/m3182-engineering-controller-active-safety-driver-residual-hard-safety-steer-delta-regression-guard-full-fresh-measurement-result-audit.md`
- source measurement: `runs/m3181_engineering_controller_active_safety_driver_residual_hard_safety_steer_delta_regression_guard_full_fresh_measurement_preflight/summary.json`
- incumbent preserved: M3105/M3103 deployable direct-action driver
- selected next route: `m3184-engineering-controller-active-safety-driver-residual-hard-safety-blocker-axis-expansion-plan`

## Evidence Summary

The M3174-M3182 branch resolved the behavior-negative M3170/M3172 regression
without producing an improvement over the incumbent:

- M3172 measured M3170 at 56 success, 6 collision, 2 offtrack, and 0
  speed-too-low on 64 full-fresh rows.
- M3172 was behavior-negative versus M3105: success -1 and collision +1.
- M3177 isolated the new regression row to M3170 steer delta: incumbent M3105
  succeeded, candidate M3170 collided, and steer-delta ablation succeeded.
- M3179 materialized an actor-visible direct-action guard that zeroes M3170
  steer delta while preserving M3170 throttle and brake deltas.
- M3181 measured M3179 at 57 success, 5 collision, 2 offtrack, and 0
  speed-too-low on the same 64 rows.
- M3181 is neutral versus M3105: success 0, collision 0, offtrack 0, and
  speed-too-low 0.
- M3181 improves over M3172 only by removing the single added collision:
  success +1 and collision -1.

The inherited blockers remain unchanged:

- collision blockers: 5
- offtrack blockers: 2
- speed-too-low blockers: 0

The actor contract remains intact:

```text
obs72 actor-visible input -> direct [steer, throttle, brake] action3
```

No hidden oracle labels, TTC, target/source/route/outcome/progress/verdict
labels, runtime base policy, checkpoint model, recurrent hidden state, or
public driver default mutation are admitted.

## Supported Claims

- M3177-M3181 identify and remove the M3170/M3172 new steer-delta collision
  regression.
- M3179 is a claim-safe direct obs72-to-action3 candidate artifact.
- M3181 restores M3105 hard-safety parity on the measured full-fresh
  denominator.
- M3105/M3103 remains the deployable incumbent.
- The residual hard-safety problem is no longer this steer-delta regression; it
  is the inherited 5 collision and 2 offtrack blockers.

## Falsified Claims

- M3179/M3181 is not a hard-safety improvement over M3105.
- M3179/M3181 is not repair success.
- M3179 is not a promotion candidate on this evidence.
- Continuing the same steer-delta guard loop is not justified.
- The residual blocker problem is not solved by local action-delta ablation.

## Failure Taxonomy Summary

- `behavior_regression`: observed for M3170/M3172 versus M3105; removed by
  M3179/M3181 on the measured denominator.
- `objective_overfit`: risk is high if the branch continues tuning around the
  single recovered row instead of moving to the remaining seven blockers.
- `contract_violation`: not observed in M3177, M3179, M3181, or M3182.
- `lineage_invalid`: avoided by preserving M3105/M3103 as incumbent.
- `metric_artifact`: not observed for M3181 row accounting; 64 measurement rows,
  128 same-row comparison rows, and 0 measurement failure rows are present.
- `scenario_sampling_failure`: unresolved outside the accepted current-sim
  denominator.
- `proof_washout`: high if M3181 parity is reworded as repair success,
  validation, or current-sim verdict.
- `seed_fragility`: unresolved beyond the measured denominator.

## Public Gate Overfit Risk

The overfit risk is high if the next branch keeps targeting the one M3172 new
regression row. That row has now served its purpose: it exposed the unsafe
steer delta and produced a regression-neutral guard. The remaining blockers
need a different evidence axis that starts from blocker families and
actor-visible state structure rather than one action-channel delta.

## Next Branch Decision

Pivot to M3184 residual hard-safety blocker axis expansion plan:

- close the steer-delta regression guard loop as complete but not promotable.
- preserve M3105/M3103 as the deployable incumbent.
- keep M3179 as an archived regression-neutral candidate artifact, not a public
  driver default replacement.
- define the next branch around the seven inherited blockers instead of the
  recovered single regression row.
- require a route plan that names which actor-visible evidence axis can change
  residual collision/offtrack evidence before any new repair implementation.

M3184 should be design/plan only. It may define blocker families, evidence
axes, allowed artifacts, stop rules, and follow-up materialization gates. It
must not execute validation, rank candidates, mutate the public driver, claim
repair success, or use hidden actor inputs.

## Claim Boundary

M3183 is synthesis and route selection only. It makes no implementation,
measurement, validation, ranking, promotion, driver-performance, current-sim
verdict, high-fidelity, full-driver, repair-success, robustness-result,
feasibility-proof, paper, finite-window-vs-GRU, or self-ID claim.
