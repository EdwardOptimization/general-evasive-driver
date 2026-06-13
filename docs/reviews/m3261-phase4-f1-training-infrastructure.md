# m3261-phase4-f1-training-infrastructure Research Review

## Summary

- Generated at UTC: 20260613T174137Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: f1_training_infrastructure_completed
- Decision reason: all F1 infrastructure gates passed; 48 mixed-regime Chrono worker steps; 2.1031 steps/s; projected 100M wall-clock 13207.81 h / 550.33 days; CUDA update speed ratio 0.00415x CPU; F2 blocked on PI wall-clock review

## Hypothesis

A preregistered Phase-4 F1 training-infrastructure milestone can prove parallel Chrono worker rollout, obs72/action3 policy smoke, finite actor-critic gradients, device feasibility re-check, and projected 100M-step wall-clock for the PI stop before validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof paper F2-training admission or self-ID claim.

## Lineage

- parent_checkpoint: docs/current-status.md, docs/roadmap-phase3-codex-execution.md, docs/m3260-phase4-e4-drift-regime-pricing.md
- parent_dataset: experiments/feasibility_audit/phase4_e1prime_spread_revival_repricing.json, experiments/feasibility_audit/phase4_e2prime_chrono_two_regime_hardened.json, experiments/feasibility_audit/phase4_e4_drift_regime_pricing.json
- parent_config: scripts/feasibility_audit/phase4_f1_training_infra_smoke.py, scripts/feasibility_audit/phase4_e2_chrono_two_regime_smoke.py, scripts/feasibility_audit/phase4_e4_drift_regime_pricing.py, scripts/feasibility_audit/chrono_worker_client.py, scripts/feasibility_audit/chrono_backend_worker.py, src/autodrift/train_ppo.py, src/autodrift/chrono_vehicle_backend.py
- parent_objective: Track F approved at full-scenario scope after E4 PI disposition, F1 only proves infrastructure, throughput, and wall-clock projection before the PI stop
- derived_from: M3258 confirmed clean-sensing belief value in Chrono at adequate power, M3259 rejected vehicle-spread reflex retuning but preserved the E1 structural gap as a full-scenario ingredient, M3260 priced drift-specialized oracle headroom in low_mu_power_oversteer at +0.4000, The roadmap marks F1 as the lowest-numbered OPEN unit after the 2026-06-14 E4 PI disposition
- blocked_by: F2 and F3 remain blocked after M3261 until PI reviews measured F1 wall-clock and gives the next go
- supersedes: treating E4 pricing alone as F2 training admission, launching a 100M-step F2 run before measuring the local Chrono worker wall-clock
- invalidates: mutating ActiveSafetyReflexDriver inside F1, writing a promotion policy checkpoint from the F1 smoke, claiming validation ranking, driver performance, current-sim sufficiency, full high-fidelity sufficiency, paper readiness, repair success, feasibility proof, F2 admission, or self-ID from M3261

## Success Criteria

- experiments/feasibility_audit/phase4_f1_training_infra_prereg.json exists before quick and full runs
- experiments/feasibility_audit/phase4_f1_training_infra_quick.json exists and passed before the full run
- experiments/feasibility_audit/phase4_f1_training_infra.json exists after the full run
- runs/feasibility_audit/phase4_f1_training_infra/worker_step_rows_full.csv includes both avoidance_clean_reveal_9p5 and drift_low_mu_power_oversteer rows
- runs/feasibility_audit/phase4_f1_training_infra/metrics_full.csv reports protocol_gates_passed=1 and f2_training_admitted=0
- docs/m3261-phase4-f1-training-infrastructure.md reports measured throughput, device re-check, projected 100M-step wall-clock, and the PI stop

## Failure Criteria

- M3261 runs full mode without preregistration or quick smoke
- M3261 omits either avoidance or drift worker rows
- M3261 violates the obs72/action3 actor contract
- M3261 reports non-finite loss or gradients or no optimizer parameter change
- M3261 fails to report throughput or projected 100M-step wall-clock
- M3261 mutates ActiveSafetyReflexDriver or writes a promotion checkpoint
- M3261 admits F2, driver performance, full high-fidelity sufficiency, paper readiness, feasibility proof, repair success, or self-ID claims

## Evidence Gates

- M3261 must write preregistration before any F1 smoke run
- M3261 must run quick smoke before the full F1 run
- M3261 must collect mixed avoidance and drift Chrono rows through worker clients
- M3261 must preserve the obs72/action3 actor contract
- M3261 must run a finite actor-critic update and change model parameters
- M3261 must record CPU device timing and CUDA timing if CUDA is available
- M3261 must report aggregate Chrono throughput and projected 100M-step wall-clock
- M3261 must keep F2 training admission false and stop for PI wall-clock review

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run full M3261 without preregistration and quick smoke
- do not launch PPO, F2, or a managed 100M-step training run
- do not write a promotion checkpoint
- do not mutate ActiveSafetyReflexDriver
- do not change obs72/action3 semantics
- do not tune the benchmark after rows are observed
- do not claim driver performance, full high-fidelity sufficiency, paper readiness, repair success, robustness result, feasibility proof, F2 admission, or self-ID from M3261

## Failure Taxonomy

- none

## Scoreboard

- milestone: m3261-phase4-f1-training-infrastructure
- type: infrastructure
- checkpoint: None
- success_rate: 1
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: f1_training_infrastructure_completed
- reason: all F1 infrastructure gates passed; 48 mixed-regime Chrono worker steps; 2.1031 steps/s; projected 100M wall-clock 13207.81 h / 550.33 days; CUDA update speed ratio 0.00415x CPU; F2 blocked on PI wall-clock review

## Next Blocker

None recorded.
