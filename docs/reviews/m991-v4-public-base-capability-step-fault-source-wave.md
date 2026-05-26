# m991-v4-public-base-capability-step-fault-source-wave Research Review

## Summary

- Generated at UTC: 20260526T132203Z
- Type: gate
- Gate tier: generalization
- Promotion decision: capability_step_source_wave_reset_only_route_to_audit
- Decision reason: M991 scales to 4096 matched pairs and finds 0 accepted wrong-history rows but 1380 reset-only rows so training remains blocked

## Hypothesis

Scaling M990 capability-step source coverage will reveal whether its steering-vs-front-authority wrong-history signal is repeatable or merely a narrow smoke artifact.

## Lineage

- parent_checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
- parent_dataset: docs/m990-v4-public-base-capability-step-fault-smoke.md, runs/m990_v4_public_base_capability_step_fault_smoke/summary.json
- parent_config: configs/m990_capability_step_fault_scenarios.json, experiments/manifests/m990-v4-public-base-capability-step-fault-smoke.json
- parent_objective: test whether M990 sparse wrong-history and reset-only signals scale under larger no-training source coverage
- derived_from: m990-v4-public-base-capability-step-fault-smoke, m989-v4-public-base-capability-step-fault-design
- blocked_by: M990 is infrastructure-positive but accepted rows are source-narrow
- supersedes: None
- invalidates: None

## Success Criteria

- summary.json exists
- scenario_count >= 3000
- snapshot_count >= 10000
- matched_pair_count >= 2500
- unique preferred fault-family groups >= 6
- unique wrong fault-family groups >= 6
- fault-family pair groups >= 10
- actor_parameters_changed == false
- training_started == false
- ppo_used == false
- promoted == false
- wrong_history_action_critical_rows and reset_only_rows are reported separately

## Failure Criteria

- checkpoint/config compatibility fails
- matched_pair_count < 2500
- actor parameters change
- hidden fault/event labels enter actor observations
- training or PPO starts
- promotion occurs
- reset-only rows are counted as accepted wrong-history rows

## Evidence Gates

- M991 must not run PPO
- M991 must not promote
- M991 must not change actor inputs
- M991 must keep hidden fault labels as logging/pairing metadata only
- M991 must report reset-only rows separately from accepted wrong-history rows
- M991 must not tune from private holdout

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not add hidden event labels to actor observations
- do not train or optimize
- do not use private holdout
- do not claim true per-wheel/asymmetric faults
- do not promote any checkpoint
- do not count reset-only rows as wrong-history proof-positive rows

## Failure Taxonomy

- scenario_sampling_failure
- metric_artifact

## Scoreboard

- milestone: m991-v4-public-base-capability-step-fault-source-wave
- type: gate
- checkpoint: runs/m991_v4_public_base_capability_step_fault_source_wave/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: capability_step_source_wave_reset_only_route_to_audit
- reason: M991 scales to 4096 matched pairs and finds 0 accepted wrong-history rows but 1380 reset-only rows so training remains blocked

## Next Blocker

m992-v4-public-base-capability-step-reset-only-audit
