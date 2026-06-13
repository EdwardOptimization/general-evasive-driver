# M3261 Phase-4 F1 Training Infrastructure

## Status

- Verdict: f1_training_infrastructure_completed
- Scope: infrastructure smoke and throughput only; no F2 launch and no driver-performance claim.

## Measured

- Parallel Chrono workers: 2
- Mixed-regime worker steps: 48 ({'avoidance_clean_reveal_9p5': 24, 'drift_low_mu_power_oversteer': 24})
- Aggregate throughput: 2.1031 steps/s
- Projected 100M-step wall-clock: 13207.81 h (550.33 days)
- Torch loss before/after: 0.004356 / 0.003224
- Grad norm: 0.102179; parameter delta L2: 0.025519
- CUDA available: True

## Gates

- preregistration_present: True
- quick_before_full: True
- chrono_worker_count_met: True
- mixed_regime_coverage: True
- obs72_contract_held: True
- action3_contract_held: True
- finite_losses: True
- finite_gradients: True
- optimizer_changed_parameters: True
- deterministic_seed_handling: True
- throughput_positive: True
- projected_wall_clock_present: True
- device_recheck_complete: True
- f2_training_admitted_false: True
- stop_for_pi_wall_clock_review: True
- all_passed: True

## Inferred

F1 proves the training-infrastructure path can collect mixed avoidance/drift Chrono rollouts, run a finite actor-critic update, and estimate 100M-step wall-clock. It does not prove driver performance or admit F2.

## Artifacts

- JSON: `experiments/feasibility_audit/phase4_f1_training_infra.json`
- Rows: `runs/feasibility_audit/phase4_f1_training_infra/worker_step_rows_full.csv`
- Metrics: `runs/feasibility_audit/phase4_f1_training_infra/metrics_full.csv`
- Preregistration: `experiments/feasibility_audit/phase4_f1_training_infra_prereg.json`

## Stop

F2/F3 remain blocked until PI reviews the F1 wall-clock/throughput report and gives the next go.
