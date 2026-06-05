# M2801 Engineering Controller Route A Source-Only Belief-Stress Clearance-Localized Candidate Fresh-Holdout Triad Delta Panel Preflight

- status: completed
- result_class: `engineering_controller_route_a_source_only_belief_stress_clearance_localized_candidate_fresh_holdout_triad_delta_panel_preflight_pass`
- manifest: `experiments/manifests/m2801-engineering-controller-route-a-source-only-belief-stress-clearance-localized-candidate-fresh-holdout-triad-delta-panel-preflight.json`
- summary: `runs/m2801_engineering_controller_route_a_source_only_belief_stress_clearance_localized_candidate_fresh_holdout_triad_delta_panel/summary.json`
- triad execution rows: `runs/m2801_engineering_controller_route_a_source_only_belief_stress_clearance_localized_candidate_fresh_holdout_triad_delta_panel/triad_execution_rows.csv`
- candidate-minus-source deltas: `runs/m2801_engineering_controller_route_a_source_only_belief_stress_clearance_localized_candidate_fresh_holdout_triad_delta_panel/candidate_minus_source_delta_rows.csv`
- candidate-minus-base deltas: `runs/m2801_engineering_controller_route_a_source_only_belief_stress_clearance_localized_candidate_fresh_holdout_triad_delta_panel/candidate_minus_base_delta_rows.csv`
- proof gates: `runs/m2801_engineering_controller_route_a_source_only_belief_stress_clearance_localized_candidate_fresh_holdout_triad_delta_panel/proof_gate_rows.csv`
- generalization holdout gates: `runs/m2801_engineering_controller_route_a_source_only_belief_stress_clearance_localized_candidate_fresh_holdout_triad_delta_panel/generalization_holdout_gate_rows.csv`
- behavior-retention gates: `runs/m2801_engineering_controller_route_a_source_only_belief_stress_clearance_localized_candidate_fresh_holdout_triad_delta_panel/behavior_retention_gate_rows.csv`
- promotion guards: `runs/m2801_engineering_controller_route_a_source_only_belief_stress_clearance_localized_candidate_fresh_holdout_triad_delta_panel/promotion_guard_rows.csv`
- follow-up manifest: `experiments/manifests/m2802-engineering-controller-route-a-source-only-belief-stress-clearance-localized-candidate-fresh-holdout-triad-delta-panel-result-audit.json`
- next: `m2802-engineering-controller-route-a-source-only-belief-stress-clearance-localized-candidate-fresh-holdout-triad-delta-panel-result-audit`

## Result

M2801 ran a bounded source-only HF0/FourWheel triad closed-loop diagnostic
panel over the M2655 source checkpoint, the M2791 start candidate, and
the M2799 clearance-localized corrective candidate. It uses fresh holdout
seed indices outside prior seed surfaces 0..11 and a longer horizon than
M2793. The rows are diagnostic deltas for audit, not ranking or winner
selection.

```text
objective_rows: 18
seed_start_index: 12
seed_count: 4
fresh_holdout_seed_indices: [12, 13, 14, 15]
previous_seed_indices: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
horizon_steps: 160
m2793_horizon_steps: 140
triad_execution_rows: 216
candidate_minus_source_delta_rows: 72
candidate_minus_base_delta_rows: 72
proof_gate_rows: 16
generalization_gate_rows: 9
behavior_retention_gate_rows: 9
promotion_guard_rows: 4
failed_gate_ids: none
```

## Candidate-Minus-Source Delta Summary

```text
candidate_minus_reference_minimum_obstacle_clearance_m: mean=-0.00365399786071096 median=-0.004516664759614875 min=-0.014554557376424304 max=0.006923733641878371 positive=23 negative=49 zero=0
candidate_minus_reference_minimum_road_margin_m: mean=0.0034070942843518006 median=0.0051379295250229 min=-0.013717438392227832 max=0.008588533356770345 positive=60 negative=12 zero=0
candidate_minus_reference_final_speed_mps: mean=0.0010017903825189295 median=0.0014799093692587917 min=-0.00816495793348615 max=0.00630289332609868 positive=49 negative=23 zero=0
candidate_minus_reference_max_abs_yaw_rate: mean=0.0028702986539291125 median=0.003020197857187046 min=-0.0006298278161761539 max=0.005960391356556682 positive=48 negative=24 zero=0
candidate_minus_reference_throttle_brake_conflict_proxy: mean=0.0 median=0.0 min=0.0 max=0.0 positive=0 negative=0 zero=72
mean_action_delta_l1: mean=0.0006010905356594814 median=0.0006267424672841878 min=0.00040634858111543437 max=0.0007621262222528383 positive=72 negative=0 zero=0
```

## Candidate-Minus-M2791-Start Delta Summary

```text
candidate_minus_reference_minimum_obstacle_clearance_m: mean=-0.001043581525003352 median=-0.0016528113121421217 min=-0.00591508324654022 max=0.0017836451484196658 positive=23 negative=49 zero=0
candidate_minus_reference_minimum_road_margin_m: mean=0.0008685596277096715 median=0.001303491179564631 min=-0.002048242314448556 max=0.0021919785625712507 positive=60 negative=12 zero=0
candidate_minus_reference_final_speed_mps: mean=0.00033127288279043306 median=0.0005978255597214321 min=-0.002463377603951322 max=0.0016326326237297017 positive=49 negative=23 zero=0
candidate_minus_reference_max_abs_yaw_rate: mean=0.0007452456651026714 median=0.0007822529462475081 min=-0.0001727918666132311 max=0.001539265359020825 positive=48 negative=24 zero=0
candidate_minus_reference_throttle_brake_conflict_proxy: mean=0.0 median=0.0 min=0.0 max=0.0 positive=0 negative=0 zero=72
mean_action_delta_l1: mean=0.00015350560209265429 median=0.00016028148432573053 min=0.00010467084745569011 max=0.0001961385210355049 positive=72 negative=0 zero=0
```

## Actor And Claim Boundary

Actor input stayed at P0 observation 72 and action 3. Atlas, role,
dynamics, stress, clearance, outcome, success, progress, route, and
verdict labels remained evaluator metadata and were not actor-visible.
Mitigation reference rows stayed outside ordinary denominators.

Obstacle-clearance and stable_avoidable retention are the hard guards
before road-margin, yaw-rate, speed, throttle/brake conflict, or
action-delta interpretation. M2801 does not train, validate, rank,
select a winner, promote a checkpoint, compute a success-rate verdict,
claim repair success, driver performance, paper evidence, current-sim
verdict, high-fidelity validation, full ideal driver completion, or
level3 self-identification.

## Route Decision

Route to M2802 result audit before interpreting the fresh-holdout triad
deltas or choosing any continuation, synthesis, repair, promotion, or stop
decision.
