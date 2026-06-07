# M3093 Active Safety Driver v2 Speed-Floor-Aware Repair Materialization Preflight

## Summary

- status: completed
- result class: `active_safety_driver_v2_speed_floor_aware_repair_materialization_preflight_pass`
- policy id: `m3093_speed_floor_aware_balanced_direct_action_repair_v2`
- rule rows: 5
- actor input exclusion rows: 10
- claim-boundary rows: 20
- gate matrix pass: True
- selected next action: `m3094-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-materialization-result-audit`

## Repair Scope

M3093 materializes a v2 speed-floor-aware balanced direct-action repair config and rule table selected by M3092. The largest M3090 behavior blocker is speed-too-low, while collision and offtrack rows remain hard-safety blockers. This materialization targets speed-floor throttle/brake release only when visible obstacle and road-edge urgency are not high, while preserving urgent obstacle and corridor recovery branches.

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

This is materialization only. M3093 runs no reset, step, rollout, replay, fitting, PPO, training, validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU comparison, or self-ID test. It makes no repair-success, robustness-result, current-sim verdict, driver-performance, full-driver, paper, or validation claim.

## Next

- next blocker: `m3094-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-materialization-result-audit`
- follow-up manifest: `experiments/manifests/m3094-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-materialization-result-audit.json`
