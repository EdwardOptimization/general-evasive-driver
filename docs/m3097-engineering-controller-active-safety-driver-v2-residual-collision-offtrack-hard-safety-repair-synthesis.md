# M3097 Active Safety Driver v2 Residual Collision/Offtrack Hard-Safety Repair Synthesis

## Synthesis Decision

- decision: `route_to_m3098_v3_high_speed_obstacle_edge_hard_safety_repair_materialization`
- synthesis status: `completed_with_residual_hard_safety_blocker`
- source measurement: `m3095-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-full-fresh-measurement-preflight`
- residual failures: `7/64`
- residual collision failures: `5`
- residual offtrack failures: `2`
- selected next action: `m3098-engineering-controller-active-safety-driver-v3-high-speed-obstacle-edge-hard-safety-direct-action-repair-materialization-preflight`

## Evidence Summary

M3095 improved the M3090 same-row measurement surface from 43 to 57 successes, removed all 11 speed-too-low terminations, and reduced offtrack from 5 to 2. It did not reduce collision count: 5 obstacle-collision failures remain. The remaining 7 failures are all T5 rows and occur only on the collision/offtrack axes:

```text
collision_lateral_intrusion: 2 collision, 1 offtrack
offtrack_boundary_recovery: 3 collision, 1 offtrack
speed_floor_stress: 0 failures
stability_action_pressure: 0 failures
```

Residual row signatures:

```text
residual mean speed: 16.956574715065464
residual mean clearance margin: 0.46409219272099683
residual mean high_sideslip_fraction: 0.20704132125184757
residual mean lateral_rmse: 1.4723631418771763
residual mean action_rate_mean: 0.06217751971312931
collision residual mean speed: 17.496280655648953
collision residual mean clearance margin: -0.18639973282244243
offtrack residual mean speed: 15.607309863606748
offtrack residual mean lateral_rmse: 2.595563685883996
```

Same-row comparison shows the v2 speed-floor repair generally increased speed on residual hard-safety rows. This was useful for speed-too-low removal, but collision rows remain high-speed and negative-clearance, while offtrack rows remain high-lateral-error and high-sideslip. The residual blocker is therefore no longer speed floor; it is high-speed hard-safety arbitration between obstacle avoidance, edge/corridor recovery, throttle suppression, and braking.

## Supported Claims

- M3095 supports a residual failure taxonomy: remaining failures are collision/offtrack only, all T5, concentrated in two hard-safety axes.
- The v2 speed-floor repair is admissible as an intermediate artifact because it preserves obs72/action3 direct action and removes speed-too-low on this denominator.
- The next repair should target high-speed obstacle and edge risk, not low-speed recovery.
- M3098 may materialize a v3 direct-action repair config/rule set that adds speed-aware obstacle/edge braking and high-risk throttle suppression before any new measurement.

## Rejected Claims

- M3095 does not prove repair success.
- M3095 does not justify validation, ranking, promotion, driver-performance, current-sim verdict, robustness-result, high-fidelity, paper, full-driver, finite-window-vs-GRU, or self-ID claims.
- Speed-floor success cannot be treated as active-safety success while 5 collision failures remain.
- The next route must not tune on hidden labels, use M3095 outcome labels as actor input, add a runtime base policy, or select only easy rows.

## Failure Taxonomy

- `contract_violation`: not observed in M3095; actor-visible obs72/action3 direct-action contract remains intact.
- `lineage_invalid`: not observed; M3097 uses M3096/M3095/M3093/M3090 artifacts.
- `metric_artifact`: not observed; residual rows, same-row deltas, summary, gate, contract, and claim artifacts exist.
- `scenario_sampling_failure`: not observed for M3095; all 64 rows are accounted.
- `behavior_regression`: collision count remains unchanged from M3090; this blocks validation or repair-success interpretation.
- `objective_overfit`: active risk if speed recovery is allowed to dominate obstacle/edge hard-safety arbitration.
- `proof_washout`: active risk if aggregate success rate hides the 5 collision rows.
- `seed_fragility`: unresolved; no broader validation should run before the residual hard-safety repair is materialized and measured.

## Public Gate Overfit Risk

Risk is medium. The synthesis is still based on the same 64-row current-sim denominator. It is sufficient to choose one bounded repair materialization route, but not sufficient for validation or promotion. The selected route must be checked by a later full-fresh measurement and then audited before any broader claim.

## Selected Repair Route

Route exactly one follow-up to:

```text
m3098-engineering-controller-active-safety-driver-v3-high-speed-obstacle-edge-hard-safety-direct-action-repair-materialization-preflight
```

M3098 should materialize a v3 direct-action repair package with these constraints:

- preserve input `obs72` only and output direct action3 `[steer, throttle, brake]`;
- preserve `runtime_base_policy_required=false`, `checkpoint_model_required=false`, and `recurrent_hidden_state_required=false`;
- add speed-aware obstacle and edge hard-safety braking for high-speed risk rows;
- suppress throttle under high obstacle urgency, high edge urgency, or combined high-speed risk;
- allow speed-floor recovery only when obstacle/edge urgency is low and speed is actually below the floor;
- keep v2 speed-floor behavior as a bounded branch, not the dominant branch under collision/offtrack risk;
- write rule/config/exclusion/claim/gate/doc artifacts only, with no rollout or validation claim.

## Boundary

M3097 is synthesis only. It runs no reset, step, rollout, replay, fitting, PPO, training, validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU comparison, or self-ID test.
