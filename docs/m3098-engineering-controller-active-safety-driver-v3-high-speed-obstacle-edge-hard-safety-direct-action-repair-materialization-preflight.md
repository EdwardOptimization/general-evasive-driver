# M3098 Active Safety Driver v3 High-Speed Obstacle/Edge Hard-Safety Repair Materialization Preflight

## Summary

- status: completed
- result class: `active_safety_driver_v3_high_speed_obstacle_edge_hard_safety_repair_materialization_preflight_pass`
- policy id: `m3098_high_speed_obstacle_edge_hard_safety_direct_action_repair_v3`
- rule rows: 5
- actor input exclusion rows: 10
- claim-boundary rows: 20
- gate matrix pass: True
- selected next action: `m3099-engineering-controller-active-safety-driver-v3-high-speed-obstacle-edge-hard-safety-direct-action-repair-materialization-result-audit`

## Repair Scope

M3098 materializes a v3 high-speed obstacle/edge hard-safety direct-action repair config and rule table selected by M3097. The remaining M3095 blockers are 5 collision and 2 offtrack rows, all T5 and concentrated in collision_lateral_intrusion/offtrack_boundary_recovery. This materialization targets high-speed obstacle and road-edge risk by increasing braking and suppressing throttle under actor-visible hard-safety urgency, while preserving the v2 speed-floor recovery branch only for low-risk low-speed states.

## Contract

```text
input: actor-visible obs72 only
output: direct action3 [steer, throttle, brake]
runtime_base_policy_required: false
checkpoint_model_required: false
recurrent_hidden_state_required: false
hidden/oracle/TTC/target/source/route/outcome/progress/verdict actor input: forbidden
```

## Boundary

This is materialization only. M3098 runs no reset, step, rollout, replay, fitting, PPO, training, validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU comparison, or self-ID test. It makes no measurement, repair-success, robustness-result, current-sim verdict, driver-performance, full-driver, paper, or validation claim.

## Next

- next blocker: `m3099-engineering-controller-active-safety-driver-v3-high-speed-obstacle-edge-hard-safety-direct-action-repair-materialization-result-audit`
- follow-up manifest: `experiments/manifests/m3099-engineering-controller-active-safety-driver-v3-high-speed-obstacle-edge-hard-safety-direct-action-repair-materialization-result-audit.json`
