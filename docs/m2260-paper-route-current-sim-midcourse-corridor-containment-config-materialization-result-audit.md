# M2260 Paper-Route Current-Sim Midcourse Corridor-Containment Config Materialization Result Audit

- status: completed
- decision: `current_sim_midcourse_corridor_containment_materialization_audit_route_to_training_execution_design`
- manifest: `experiments/manifests/m2260-paper-route-current-sim-midcourse-corridor-containment-config-materialization-result-audit.json`
- parent result: `runs/m2259_paper_route_current_sim_midcourse_corridor_containment_configs/summary.json`

## Audit Result

M2259 is a clean targeted containment config materialization:

```text
result_class: current_sim_midcourse_corridor_containment_config_materialization_pass
materialized_config_count: 15
training_matrix_row_count: 15
profile_set_matched: true
seed_set_matched: true
budget_signature_count: 1
target_value_mismatch_count: 0
contract_violation_count: 0
track_width_widened_count: 0
guardrail_violation_count: 0
```

The training matrix contains exactly:

```text
profiles:
  L0_current_masked
  L1_one_step
  L2_window_25
  L2_window_50
  L3_online_gru

seeds:
  222601
  222602
  222603
```

The shared target tuple is:

```text
track_width: 8.5
track_cost_scale: 3.0
heading_cost_scale: 0.3
road_margin_cost_scale: 2.6
road_margin_warning_fraction: 0.5
off_track_penalty: 8.0
```

The actor contract remains:

```text
input_contract: P0_human_view_no_wheel_no_oracle
include_privileged_params: false
wheel_observation_mode: none
obstacle_relative_velocity_mode: zero
```

## Route Decision

M2259 passes the materialization audit and admits a bounded training-execution
design. The next step should freeze an execution command over:

```text
runs/m2259_paper_route_current_sim_midcourse_corridor_containment_configs/training_matrix.csv
```

The execution design should keep the candidate-checkpoint runner pattern used
by M2241/M2250:

```text
15 train_ppo jobs
32768 total_steps each
checkpoint_interval_steps 4096
8 candidate checkpoints per run
120 candidate eval rows
15 selected checkpoint rows
```

Interpretation must remain blocked until a post-execution audit and later
selected-checkpoint outcome localization compare against M2244/M2253 style
episode rows.

## Blocked Routes

Blocked for now:

```text
starting training inside M2260
direct controller-family ranking
winner selection
finite-window-vs-GRU conclusion
paper-level result
level3 self-identification claim
changing actor inputs
widening track_width
accepting return improvement without slice outcome localization
```

## Next

Pre-register:

```text
m2261-paper-route-current-sim-midcourse-corridor-containment-training-execution-design
```

M2261 should design the execution command only. M2262 can run training if the
design passes.
