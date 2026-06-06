# M2869 Engineering Controller Route A Localized Response-Prediction Candidate Closed-Loop Delta Panel Result Audit

## Metadata

- status: completed
- decision: `accept_m2868_diagnostic_delta_panel_route_to_m2870_branch_synthesis`
- parent milestone: `m2868-engineering-controller-route-a-response-predictive-recurrent-belief-localized-response-prediction-candidate-closed-loop-delta-panel-preflight`
- parent summary: `runs/m2868_engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_candidate_closed_loop_delta_panel/summary.json`
- parent paired execution rows: `runs/m2868_engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_candidate_closed_loop_delta_panel/paired_execution_rows.csv`
- parent paired delta rows: `runs/m2868_engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_candidate_closed_loop_delta_panel/paired_delta_rows.csv`
- parent surface delta rows: `runs/m2868_engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_candidate_closed_loop_delta_panel/surface_delta_rows.csv`
- parent gate matrix: `runs/m2868_engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_candidate_closed_loop_delta_panel/gate_matrix.csv`
- follow-up manifest: `experiments/manifests/m2870-engineering-controller-route-a-response-predictive-recurrent-belief-localized-response-prediction-branch-synthesis.json`

## Audit Result

M2869 accepts M2868 as a complete and claim-safe bounded diagnostic delta panel.

The accepted artifact facts are:

```text
status_pass: true
gate_matrix_pass: true
failed_gate_ids: none
paired execution rows: 48
paired delta rows: 24
surface delta rows: 2
surface counts: m2850_explanatory 16, fresh_disjoint 8
execution status: completed 48
actor contract: 72 observation / 3 action preserved
actor-visible labels: false
hidden/oracle actor input: false
ordinary success denominator allowed: false
ranking/winner/promotion/success-rate verdict: false
```

M2868 also fixed the M2866 lineage guard to read the actor-contract evidence from
the M2866 checkpoint manifest and actor guard rows rather than from the M2866
summary alone. The accepted lineage evidence is:

```text
M2866 status_pass: true
M2866 gate_matrix_pass: true
M2866 candidate checkpoint written: true
M2866 response_prediction_loss_mean: 0.24616368114948273
M2866 manifest actor_contract_shape_72_action_3: true
M2866 actor guard rows pass: true
M2866 actor-visible labels: false
M2866 hidden/oracle actor input: false
```

## Closed-Loop Delta Reading

The M2868 panel is diagnostic evidence, not validation evidence.

Observed terminal outcomes did not improve:

```text
baseline rows: 24, success 0, collision 1
candidate rows: 24, success 0, collision 1
termination counts baseline: blank 19, speed_too_low 4, obstacle_collision 1
termination counts candidate: blank 19, speed_too_low 4, obstacle_collision 1
termination_pair_changed_count: 0 on both surfaces
collision_pair_changed_count: 0 on both surfaces
```

Surface-separated diagnostic deltas were small and mixed:

```text
fresh_disjoint rows: 8
  mean candidate-baseline clearance margin: +0.011514063063262692
  mean candidate-baseline return: -0.15161537536197656
  mean candidate-baseline speed: -0.01335838212578161
  mean candidate-baseline high sideslip: -0.00474740849996998

m2850_explanatory rows: 16
  mean candidate-baseline clearance margin: +0.020778703978062613
  mean candidate-baseline return: -0.014369599207990802
  mean candidate-baseline speed: -0.010273789673540784
  mean candidate-baseline high sideslip: +0.0007573888984214149
```

This supports only the narrow statement that the M2866 candidate produced
complete paired closed-loop diagnostic deltas with slightly higher mean
clearance margin and lower mean return/speed on the audited surfaces. It does
not support a repair-success, validation-readiness, driver-performance, paper,
current-sim, high-fidelity, full-driver, or self-ID claim.

## Decision

M2869 accepts the M2868 artifacts and routes to M2870 branch synthesis.

The reason is that M2868 is artifact-complete and claim-safe, but the closed-loop
deltas do not justify direct promotion or another local training step. The
candidate did not change success/collision terminal outcomes on this diagnostic
panel, and its surface deltas are mixed. Continuing without synthesis would risk
optimizing the localized response-prediction branch around fixed diagnostic
surfaces rather than moving Route A toward a usable actuator-level controller
baseline under the post-M2470 route split.

## Claim Boundary

Allowed claim:

```text
M2868 produced complete paired M2848-source versus M2866-candidate closed-loop
diagnostic artifacts over 16 M2850 explanatory and 8 fresh/disjoint rows under
unchanged actor and claim boundaries.
```

Forbidden interpretations:

```text
validation result
checkpoint ranking
winner selection
checkpoint promotion
success-rate verdict
repair success
driver performance
paper evidence
finite-window-vs-GRU conclusion
current-sim verdict
high-fidelity validation
full ideal driver completion
level3 self-identification
```

## Next Blocker

`m2870-engineering-controller-route-a-response-predictive-recurrent-belief-localized-response-prediction-branch-synthesis`
