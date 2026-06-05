# M2787 Engineering Controller Route A Source-Only Belief-Stress Fresh-Holdout Delta Panel Preflight

- status: completed
- result_class: `engineering_controller_route_a_source_only_belief_stress_fresh_holdout_delta_panel_preflight_pass`
- manifest: `experiments/manifests/m2787-engineering-controller-route-a-source-only-belief-stress-fresh-holdout-delta-panel-preflight.json`
- summary: `runs/m2787_engineering_controller_route_a_source_only_belief_stress_fresh_holdout_delta_panel/summary.json`
- paired execution rows: `runs/m2787_engineering_controller_route_a_source_only_belief_stress_fresh_holdout_delta_panel/paired_execution_rows.csv`
- paired delta rows: `runs/m2787_engineering_controller_route_a_source_only_belief_stress_fresh_holdout_delta_panel/paired_delta_rows.csv`
- proof retention gates: `runs/m2787_engineering_controller_route_a_source_only_belief_stress_fresh_holdout_delta_panel/proof_retention_gate_rows.csv`
- generalization holdout gates: `runs/m2787_engineering_controller_route_a_source_only_belief_stress_fresh_holdout_delta_panel/generalization_holdout_gate_rows.csv`
- promotion guards: `runs/m2787_engineering_controller_route_a_source_only_belief_stress_fresh_holdout_delta_panel/promotion_guard_rows.csv`
- follow-up manifest: `experiments/manifests/m2788-engineering-controller-route-a-source-only-belief-stress-fresh-holdout-delta-panel-result-audit.json`
- next: `m2788-engineering-controller-route-a-source-only-belief-stress-fresh-holdout-delta-panel-result-audit`

## Result

M2787 ran a bounded source-only HF0/FourWheel paired closed-loop diagnostic
panel over the M2655 source checkpoint and the M2782 candidate checkpoint.
It uses fresh holdout seed indices outside M2784 seed_index 0..3 and a
longer horizon than M2784. The rows are candidate-vs-source deltas for
audit, not a ranking or winner selection.

```text
curriculum_rows: 18
seed_start_index: 4
seed_count: 4
fresh_holdout_seed_indices: [4, 5, 6, 7]
m2784_seed_indices: [0, 1, 2, 3]
horizon_steps: 120
m2784_horizon_steps: 80
paired_execution_rows: 144
paired_delta_rows: 72
proof_gate_rows: 13
generalization_gate_rows: 8
promotion_guard_rows: 4
failed_gate_ids: none
```

## Delta Summary

```text
candidate_minus_source_minimum_obstacle_clearance_m: mean=0.00035927758389157286 median=0.0012294839614694908 min=-0.0037394441382763155 max=0.005563442547770414 positive=43 negative=29 zero=0
candidate_minus_source_minimum_road_margin_m: mean=0.003045548777864837 median=0.003106116556409022 min=0.0017406585947428166 max=0.004875049267406784 positive=72 negative=0 zero=0
candidate_minus_source_final_speed_mps: mean=0.0026159244394306303 median=0.0033156956468582965 min=-0.004601285240803277 max=0.005643853462414361 positive=63 negative=9 zero=0
candidate_minus_source_max_abs_yaw_rate: mean=-0.00017877287320032365 median=-0.00024961173037246764 min=-0.0010484951493790473 max=0.0017912210375098936 positive=7 negative=60 zero=5
candidate_minus_source_throttle_brake_conflict_proxy: mean=0.0 median=0.0 min=0.0 max=0.0 positive=0 negative=0 zero=72
mean_action_delta_l1: mean=0.000330366297728483 median=0.00031615644693372413 min=0.00026067660914526797 max=0.0005429464909765628 positive=72 negative=0 zero=0
```

## Actor And Claim Boundary

Actor input stayed at P0 observation 72 and action 3. Stress, admission,
curriculum, role, dynamics, outcome, success, progress, route, and verdict
labels remained evaluator metadata and were not actor-visible. Mitigation
reference rows stayed outside ordinary denominators.

M2787 does not train, validate, rank, select a winner, promote a checkpoint,
compute a success-rate verdict, claim repair success, driver performance,
paper evidence, current-sim verdict, high-fidelity validation, full ideal
driver completion, or level3 self-identification.

## Route Decision

Route to M2788 result audit before interpreting the fresh-holdout paired
deltas or choosing any continuation, synthesis, repair, or stop decision.
