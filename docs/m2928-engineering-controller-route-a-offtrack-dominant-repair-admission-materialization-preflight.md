# M2928 Engineering Controller Route A Offtrack-Dominant Repair Admission Materialization Preflight

## Summary

- status: completed
- result class: `engineering_controller_route_a_offtrack_dominant_repair_admission_materialization_preflight_pass`
- denominator rows preserved: 56
- offtrack rows preserved: 38
- non-offtrack context rows preserved: 18
- repair hypothesis rows: 4
- coverage constraint rows: 27
- shortcut exclusion rows: 7
- guardrails preserved: True
- gate matrix pass: True

## Coverage Constraints

- source counts: {'m2737': 12, 'm2746': 10, 'm2807': 8, 'm2816': 8}
- task counts: {'T4': 21, 'T5': 17}
- checkpoint context counts: {'m2655_mitigation_preserving_checkpoint': 10, 'public_pilot_l3_checkpoint': 28}
- environment counts: {'t4_actuator_delay_response': 8, 't4_capability_step_temporal': 9, 't4_staged_warmup_capability': 4, 't5_boundary_axis_retarget': 5, 't5_near_boundary_warmup': 12}
- window counts: {'decision_minus_24': 4, 'decision_minus_32': 5, 'mapping_window_unspecified': 20, 'reveal_plus_4': 9}
- overshoot bands: {'high_overshoot_gt_0p08': 13, 'low_overshoot_le_0p02': 5, 'medium_overshoot_le_0p08': 20}
- time bands: {'early_le_1p75s': 9, 'late_gt_2p5s': 9, 'mid_le_2p5s': 20}

## Boundary

M2928 materializes repair-admission rows only. Coverage rows are constraints, not rankings. It does not rerun environments, train, validate, rank, promote, or claim repair success.

Rejected claims:

```text
repair success, driver performance, validation readiness or result, source/task/checkpoint/environment/window/severity/time-band ranking, winner selection, checkpoint promotion, success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, current-sim verdict, high-fidelity validation readiness or result, full ideal driver completion, or level3 self-identification
```

## Next

- next blocker: `m2929-engineering-controller-route-a-offtrack-dominant-repair-admission-materialization-result-audit`
- follow-up manifest: `experiments/manifests/m2929-engineering-controller-route-a-offtrack-dominant-repair-admission-materialization-result-audit.json`
