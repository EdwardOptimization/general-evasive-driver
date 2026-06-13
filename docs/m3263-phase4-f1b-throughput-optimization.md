# M3263 Phase-4 F1b Throughput Optimization

## Status

- Verdict: f1b_throughput_target_met
- Scope: throughput optimization and wall-clock reprojection only; no F2 launch and no driver-performance claim.
- Remaining bottleneck: target_met_stop_for_pi

## Measured

- Chrono workers: 30 (default full target 30)
- Steps per unit: 32; batch horizon: 8
- Closed-loop one-step throughput: 1600.8440 steps/s
- Batched action-sequence throughput: 1967.0045 steps/s
- Best aggregate throughput: 1967.0045 steps/s
- Speedup vs F1 baseline: 935.27x
- Projected 100M-step wall-clock from best path: 14.12 h (0.59 days)
- PI target: 1000.0 steps/s (27.78 h for 100M)
- Mixed-regime worker steps: 1920 ({'avoidance_clean_reveal_9p5': 960, 'drift_low_mu_power_oversteer': 960})

## Gates

- preregistration_present: True
- quick_before_full: True
- worker_count_scaled: True
- mixed_regime_coverage: True
- closed_loop_protocol_exercised: True
- batched_transport_protocol_exercised: True
- obs72_contract_held: True
- action3_contract_held: True
- determinism_replay_passed: True
- throughput_positive: True
- projected_wall_clock_present: True
- target_1000_steps_per_s_met: True
- target_miss_reportable: True
- f2_training_admitted_false: True
- stop_for_pi_wall_clock_review: True
- all_passed: True

## Inferred

F1b reports whether worker scaling plus batched IPC makes the F2 calendar-cost target plausible. A target miss is a completed negative throughput result, not permission to start F2.

## Artifacts

- JSON: `experiments/feasibility_audit/phase4_f1b_throughput.json`
- Rows: `runs/feasibility_audit/phase4_f1b_throughput/worker_step_rows_full.csv`
- Metrics: `runs/feasibility_audit/phase4_f1b_throughput/metrics_full.csv`
- Preregistration: `experiments/feasibility_audit/phase4_f1b_throughput_prereg.json`

## Stop

F2/F3 remain blocked until PI reviews the F1b throughput report and gives the next go.
