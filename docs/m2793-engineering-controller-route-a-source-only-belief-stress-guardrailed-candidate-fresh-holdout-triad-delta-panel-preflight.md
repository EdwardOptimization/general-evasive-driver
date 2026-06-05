# M2793 Engineering Controller Route A Source-Only Belief-Stress Guardrailed Candidate Fresh-Holdout Triad Delta Panel Preflight

- status: completed
- result_class: `engineering_controller_route_a_source_only_belief_stress_guardrailed_candidate_fresh_holdout_triad_delta_panel_preflight_pass`
- manifest: `experiments/manifests/m2793-engineering-controller-route-a-source-only-belief-stress-guardrailed-candidate-fresh-holdout-triad-delta-panel-preflight.json`
- summary: `runs/m2793_engineering_controller_route_a_source_only_belief_stress_guardrailed_candidate_fresh_holdout_triad_delta_panel/summary.json`
- triad execution rows: `runs/m2793_engineering_controller_route_a_source_only_belief_stress_guardrailed_candidate_fresh_holdout_triad_delta_panel/triad_execution_rows.csv`
- candidate-minus-source deltas: `runs/m2793_engineering_controller_route_a_source_only_belief_stress_guardrailed_candidate_fresh_holdout_triad_delta_panel/candidate_minus_source_delta_rows.csv`
- candidate-minus-base deltas: `runs/m2793_engineering_controller_route_a_source_only_belief_stress_guardrailed_candidate_fresh_holdout_triad_delta_panel/candidate_minus_base_delta_rows.csv`
- proof gates: `runs/m2793_engineering_controller_route_a_source_only_belief_stress_guardrailed_candidate_fresh_holdout_triad_delta_panel/proof_gate_rows.csv`
- generalization holdout gates: `runs/m2793_engineering_controller_route_a_source_only_belief_stress_guardrailed_candidate_fresh_holdout_triad_delta_panel/generalization_holdout_gate_rows.csv`
- behavior-retention gates: `runs/m2793_engineering_controller_route_a_source_only_belief_stress_guardrailed_candidate_fresh_holdout_triad_delta_panel/behavior_retention_gate_rows.csv`
- promotion guards: `runs/m2793_engineering_controller_route_a_source_only_belief_stress_guardrailed_candidate_fresh_holdout_triad_delta_panel/promotion_guard_rows.csv`
- follow-up manifest: `experiments/manifests/m2794-engineering-controller-route-a-source-only-belief-stress-guardrailed-candidate-fresh-holdout-triad-delta-panel-result-audit.json`
- next: `m2794-engineering-controller-route-a-source-only-belief-stress-guardrailed-candidate-fresh-holdout-triad-delta-panel-result-audit`

## Result

M2793 ran a bounded source-only HF0/FourWheel triad closed-loop diagnostic
panel over the M2655 source checkpoint, the M2782 base candidate, and the
M2791 guardrailed candidate. It uses fresh holdout seed indices outside
M2784 seed_index 0..3 and M2787 seed_index 4..7, and a longer horizon than
M2787. The rows are diagnostic deltas for audit, not ranking or winner
selection.

```text
objective_rows: 18
seed_start_index: 8
seed_count: 4
fresh_holdout_seed_indices: [8, 9, 10, 11]
previous_seed_indices: [0, 1, 2, 3, 4, 5, 6, 7]
horizon_steps: 140
m2787_horizon_steps: 120
triad_execution_rows: 216
candidate_minus_source_delta_rows: 72
candidate_minus_base_delta_rows: 72
proof_gate_rows: 16
generalization_gate_rows: 9
behavior_retention_gate_rows: 6
promotion_guard_rows: 4
failed_gate_ids: none
```

## Candidate-Minus-Source Delta Summary

```text
candidate_minus_reference_minimum_obstacle_clearance_m: mean=-0.0003189920460919861 median=-0.0026030437199309198 min=-0.006653873890877904 max=0.011410545190809529 positive=30 negative=42 zero=0
candidate_minus_reference_minimum_road_margin_m: mean=0.0034386080322648363 median=0.00372921837408291 min=0.0010411562825525245 max=0.004971390708701229 positive=72 negative=0 zero=0
candidate_minus_reference_final_speed_mps: mean=0.003411489771898279 median=0.003972710138293367 min=0.0004736752793697008 max=0.004814530529195338 positive=72 negative=0 zero=0
candidate_minus_reference_max_abs_yaw_rate: mean=0.000749332315266252 median=-0.00012169519104787696 min=-0.0005615673461485948 max=0.003626609654885038 positive=31 negative=41 zero=0
candidate_minus_reference_throttle_brake_conflict_proxy: mean=0.0 median=0.0 min=0.0 max=0.0 positive=0 negative=0 zero=72
mean_action_delta_l1: mean=0.0004111395725024422 median=0.0004064562774839982 min=0.0002909995260692577 max=0.0006060793286278102 positive=72 negative=0 zero=0
```

## Candidate-Minus-Base Delta Summary

```text
candidate_minus_reference_minimum_obstacle_clearance_m: mean=-0.00013214111660788612 median=-0.00039442807985579087 min=-0.00235656386714167 max=0.0022516642629391015 positive=29 negative=43 zero=0
candidate_minus_reference_minimum_road_margin_m: mean=0.0005574076583107706 median=0.0005734233075074258 min=-0.0008686897296104057 max=0.001608095334954207 positive=71 negative=1 zero=0
candidate_minus_reference_final_speed_mps: mean=0.0005114971257720868 median=0.0006114056618961028 min=-0.0008592858191018848 max=0.0012892709511707068 positive=70 negative=2 zero=0
candidate_minus_reference_max_abs_yaw_rate: mean=0.00011760097164286581 median=-1.9362223364738362e-05 min=-8.728618770531549e-05 max=0.0005534231488594221 positive=31 negative=41 zero=0
candidate_minus_reference_throttle_brake_conflict_proxy: mean=0.0 median=0.0 min=0.0 max=0.0 positive=0 negative=0 zero=72
mean_action_delta_l1: mean=6.113127268180232e-05 median=6.196321476072594e-05 min=1.510764871322697e-05 max=0.00011067901338849644 positive=72 negative=0 zero=0
```

## Actor And Claim Boundary

Actor input stayed at P0 observation 72 and action 3. Stress, admission,
curriculum, role, dynamics, outcome, success, progress, route, and verdict
labels remained evaluator metadata and were not actor-visible. Mitigation
reference rows stayed outside ordinary denominators.

Obstacle-clearance retention is the hard guard before road-margin, yaw-rate,
speed, throttle/brake conflict, or action-delta interpretation. M2793 does
not train, validate, rank, select a winner, promote a checkpoint, compute a
success-rate verdict, claim repair success, driver performance, paper
evidence, current-sim verdict, high-fidelity validation, full ideal driver
completion, or level3 self-identification.

## Route Decision

Route to M2794 result audit before interpreting the fresh-holdout triad
deltas or choosing any continuation, synthesis, repair, promotion, or stop
decision.
