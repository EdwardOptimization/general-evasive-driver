# M3078 Active Safety Driver v1 Actor-Visible Deterministic Direct-Action Safety-Reflex Materialization Preflight

## Summary

- status: completed
- result class: `active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_materialization_preflight_pass`
- feature contract rows: 6
- safety-reflex rule rows: 6
- actor-input exclusion rows: 10
- measurement admission rows: 12
- claim-boundary rows: 19
- gate matrix pass: True

## Interpretation

M3078 materializes one actor-visible deterministic direct-action safety-reflex skeleton. The skeleton maps the canonical P0 obs72 frame to clipped `[steer, throttle, brake]` without a runtime base policy. This is contract and route materialization only; it is not rollout, validation, ranking, promotion, repair-success, driver-performance, high-fidelity, paper, finite-window-vs-GRU, full-driver, or self-ID evidence.

Selected feature groups:

```text
ego_response obs[0:5]
actuator_state obs[5:9]
previous_action obs[9:12]
road_left_boundary obs[12:28]
road_right_boundary obs[28:44]
obstacle_slots obs[44:72]
```

Rule families:

```text
collision approach braking
collision lateral avoidance
offtrack corridor centering
offtrack edge braking
stability damping
bounded direct-action clipping
```

Rejected claims:

```text
validation result, driver-performance verdict, current-sim verdict, repair success, checkpoint ranking, winner selection, checkpoint promotion, high-fidelity validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, full ideal driver completion, or level3 self-identification
```

## Next

- next blocker: `m3079-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-materialization-result-audit`
- follow-up manifest: `experiments/manifests/m3079-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-materialization-result-audit.json`
