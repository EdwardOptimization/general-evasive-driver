# m1375-paper-route-promoted-base-source-rich-public-wave Research Review

## Summary

- Generated at UTC: 20260528T214312Z
- Type: gate
- Gate tier: generalization
- Promotion decision: promoted_base_source_rich_public_wave_pass_sparse_source_route_to_audit
- Decision reason: M1375 larger source-rich wave passes structurally but remains sparse with 3 accepted rows and 1281 reset-only rows

## Hypothesis

A larger promoted-base public source-rich wave can determine whether the sparse M1373 wrong-history positives repeat under fresh broader coverage.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: docs/m1374-paper-route-promoted-base-source-rich-smoke-result-audit.md, runs/m1373_promoted_base_source_rich_smoke/summary.json, configs/m991_capability_step_fault_source_wave.json, docs/m991-v4-public-base-capability-step-fault-source-wave.md
- parent_config: experiments/manifests/m1374-paper-route-promoted-base-source-rich-smoke-result-audit.json, configs/m991_capability_step_fault_source_wave.json
- parent_objective: run a larger no-training promoted-base source-rich public wave to test whether M1373 sparse wrong-history positives repeat
- derived_from: m1374-paper-route-promoted-base-source-rich-smoke-result-audit
- blocked_by: M1374 audits M1373 as structurally clean but source-positive evidence remains one-seed sparse
- supersedes: training from M1373 sparse rows, using private holdout before public source-rich scaling, claiming source-diverse proof from the M1373 smoke
- invalidates: None

## Success Criteria

- runs/m1375_promoted_base_source_rich_public_wave/summary.json exists
- scenario_count > 0
- snapshot_count > 0
- matched_pair_count > 0
- actor_parameters_changed == false
- training_started == false
- ppo_used == false
- promoted == false
- pairing_mode == cross_fault
- model_fidelity_limits.md exists
- accepted and reset-only row counts are reported against pre-registered interpretation thresholds

## Failure Criteria

- summary or core CSV artifacts are missing
- scenario_count, snapshot_count, or matched_pair_count is zero
- actor parameters or actor inputs change
- training, PPO, promotion, or private holdout occurs
- source-positive thresholds are relaxed after seeing results
- future-only high-fidelity faults are reported as executed physical claims

## Evidence Gates

- M1375 must run the promoted M1362 base through the larger public capability-step source wave
- M1375 must keep actor inputs and checkpoint parameters unchanged
- M1375 must produce source-rich scenario, pair, intervention, accepted, reset-only, rejected, and model-fidelity artifacts
- M1375 must keep private holdout unused
- M1375 must interpret accepted-row sparsity using the pre-registered thresholds

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not mutate the candidate checkpoint
- do not relax source-positive thresholds after results
- do not claim true high-fidelity per-wheel physics

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1375-paper-route-promoted-base-source-rich-public-wave
- type: gate
- checkpoint: runs/m1375_promoted_base_source_rich_public_wave/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: promoted_base_source_rich_public_wave_pass_sparse_source_route_to_audit
- reason: M1375 larger source-rich wave passes structurally but remains sparse with 3 accepted rows and 1281 reset-only rows

## Next Blocker

m1376-paper-route-promoted-base-source-rich-public-wave-result-audit
