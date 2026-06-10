# M3117 Residual Action Influence Repair Synthesis

## Decision

- synthesis decision: `continue`
- decision: `route_to_m3118_residual_trajectory_authority_stability_recovery_repair_materialization`
- selected next action: `m3118-engineering-controller-active-safety-driver-residual-trajectory-authority-stability-recovery-repair-materialization-preflight`
- reason: M3115 shows the residual failures are not caused by missing hard-safety signal or missing action output. All seven rows have actor-visible hard-safety signal and nonzero direct action. The next repair must change the mechanism from late/high-gain overlay to actor-visible early trajectory authority and stability-recovery allocation.

## Evidence Summary

M3115 is complete and claim-safe as a diagnostic trace artifact:

```text
residual rows: 7/7
step trace rows: 256
action influence rows: 7
trace failures: 0
terminal collisions: 5
terminal offtracks: 2
terminal successes: 0
hard-safety signal present rows: 7
```

The diagnostic labels are:

```text
collision_action_present_but_clearance_unresolved: 5
offtrack_stability_recovery_limited: 2
```

The aggregate action evidence is:

```text
mean final-window brake physical: 0.7223248262490545
mean final-window absolute steer: 0.8971640084471021
mean action saturation fraction: 0.230531191232729
max obstacle urgency: 0.7579162245811707
max edge urgency: 0.9952551261521876
```

The row-level timing evidence separates the residuals into two mechanisms:

```text
collision rows:
- m3084-measurement-episode-0007: first obstacle urgency > 0.1 at step 27, first brake > 0.55 at step 27, terminal speed 17.20925052001461
- m3084-measurement-episode-0010: first obstacle urgency > 0.1 at step 23, first brake > 0.55 at step 10, terminal speed 15.656857594621808
- m3084-measurement-episode-0025: first obstacle urgency > 0.1 at step 23, first brake > 0.55 at step 23, terminal speed 14.147933466316514
- m3084-measurement-episode-0026: first obstacle urgency > 0.1 at step 23, first brake > 0.55 at step 18, terminal speed 18.703511856560457
- m3084-measurement-episode-0029: first obstacle urgency > 0.1 at step 15, first brake > 0.55 at step 15, terminal speed 18.290105713966845

offtrack rows:
- m3084-measurement-episode-0013: edge urgency > 0.2 from step 1, high sideslip fraction 0.5192307692307693, terminal lateral error 5.138059865672094
- m3084-measurement-episode-0024: edge urgency > 0.2 from step 1, high sideslip fraction 0.2549019607843137, terminal lateral error 5.140619697665997
```

The deployable actor contract remains intact:

```text
input: actor-visible obs72 only
output: direct action3 [steer, throttle, brake]
runtime_base_policy_required: false
checkpoint_model_required: false
recurrent_hidden_state_required: false
hidden/oracle/TTC/target/source/route/outcome/progress/verdict actor input: forbidden
```

## Supported Claims

- M3115 provides complete row-preserving diagnostic trace evidence for the seven residual M3112 failures.
- The residual failures are not explained by absent actor-visible hard-safety signal.
- The residual failures are not explained by absent action output: final-window steer and brake are already substantial.
- Collision rows point to clearance-trajectory authority or action timing under late/near-obstacle visibility, not to a simple missing-brake bug.
- Offtrack rows point to stability recovery under sustained edge urgency and sideslip, not to missing edge signal.
- A next materialization can be justified only if it changes the mechanism: early actor-visible obstacle corridor commitment, brake/throttle timing, and stability-biased steering authority allocation.

## Falsified Claims

- M3115 is not repair-success evidence.
- M3115 does not prove that increasing residual overlay gains will reduce collision or offtrack counts.
- M3115 does not justify validation, ranking, promotion, current-sim verdict, robustness-result, high-fidelity, paper, full-driver, or self-ID claims.
- A direct continuation of the previous overlay strategy without changing timing and stability allocation would not change the evidence axis.

## Failure Taxonomy Summary

- `contract_violation`: not observed; obs72/action3 direct-action boundary is preserved.
- `lineage_invalid`: not observed; M3117 routes from M3116/M3115/M3114 evidence.
- `metric_artifact`: not observed; trace rows, action influence rows, claim rows, and gate matrix are complete.
- `scenario_sampling_failure`: not observed for the seven residual rows; broader validation remains unclaimed.
- `behavior_regression`: still observed relative to the full objective because 5 collision and 2 offtrack residual failures remain.
- `objective_overfit`: high risk if the next route only retunes known-row overlay gains.
- `proof_washout`: high risk if diagnostic action labels are described as repair success.
- `seed_fragility`: unresolved; no generalization or validation route is justified before a repair mechanism is materialized and measured.

## Public Gate Overfit Risk

Risk is high if M3118 only increases existing obstacle or edge gains. M3115 shows final-window action is already large, with saturation on multiple collision rows. The next route must explicitly prevent same-row overfit by materializing mechanism-level rules and guards:

- earlier use of actor-visible obstacle slot geometry before the existing urgency becomes large
- trajectory/corridor authority rather than only more brake
- stability-aware steering allocation when high sideslip and edge urgency coexist
- speed-floor preservation so the M3105/M3112 zero speed-too-low property is not lost
- full-fresh measurement only after a separate audit accepts the materialization

## Next Branch Decision

Continue to:

```text
m3118-engineering-controller-active-safety-driver-residual-trajectory-authority-stability-recovery-repair-materialization-preflight
```

M3118 should be a materialization-only milestone. It should define an obs72-to-action3 direct-action policy variant derived from M3115:

- early obstacle corridor commitment from actor-visible obstacle slots and road boundary features
- brake/throttle timing that starts before terminal collision geometry rather than only in the final near-obstacle window
- stability-biased steering authority allocation that avoids simply saturating steering during high sideslip
- speed-floor preservation below the existing guard threshold
- actor-input exclusion rows forbidding hidden TTC, target, source, route, outcome, success-progress, and verdict labels
- claim-boundary rows forbidding repair-success, validation, ranking, promotion, performance, high-fidelity, full-driver, robustness-result, paper, and self-ID claims

The branch remains:

```text
active_safety_driver_residual_step_action_influence_diagnosis
```

M3118 must register M3119 result audit before any full-fresh measurement.

## Boundary

M3117 is a synthesis decision only. It runs no reset, step, rollout, replay, fitting, PPO, training, validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU comparison, or self-ID test.
