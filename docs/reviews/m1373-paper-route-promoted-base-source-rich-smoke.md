# m1373-paper-route-promoted-base-source-rich-smoke Research Review

## Summary

- Generated at UTC: 20260528T213108Z
- Type: gate
- Gate tier: generalization
- Promotion decision: promoted_base_source_rich_smoke_pass_sparse_source_route_to_audit
- Decision reason: M1373 source-rich smoke passes structurally with 832 scenarios 768 matched pairs 2 accepted rows and 174 reset-only rows

## Hypothesis

The promoted M1362 public-gate base can be evaluated through the public capability-step cross-fault harness without actor mutation, private holdout, or proxy-physics overclaiming.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: docs/m1372-paper-route-promoted-base-source-rich-generalization-design.md, configs/m990_capability_step_fault_scenarios.json, docs/m990-v4-public-base-capability-step-fault-smoke.md, docs/m998-v4-public-base-capability-step-fault-generation-synthesis.md
- parent_config: experiments/manifests/m1372-paper-route-promoted-base-source-rich-generalization-design.json, configs/m990_capability_step_fault_scenarios.json
- parent_objective: run a no-training promoted-base source-rich public smoke through the capability-step cross-fault harness
- derived_from: m1372-paper-route-promoted-base-source-rich-generalization-design
- blocked_by: M1372 admits a no-training source-rich smoke before larger source-rich waves or L0/L1/L2/L3 comparison refresh
- supersedes: using source-rich configs without claim-boundary audit, using private holdout for source-rich debugging, routing directly from public-base promotion to PPO continuation
- invalidates: None

## Success Criteria

- runs/m1373_promoted_base_source_rich_smoke/summary.json exists
- scenario_count > 0
- snapshot_count > 0
- matched_pair_count > 0
- actor_parameters_changed == false
- training_started == false
- ppo_used == false
- promoted == false
- pairing_mode == cross_fault
- model_fidelity_limits.md exists
- scenario and pair CSV artifacts are readable

## Failure Criteria

- summary or core CSV artifacts are missing
- scenario_count, snapshot_count, or matched_pair_count is zero
- actor parameters or actor inputs change
- training, PPO, promotion, or private holdout occurs
- future-only high-fidelity faults are reported as executed physical claims

## Evidence Gates

- M1373 must run the promoted M1362 base through the public capability-step cross-fault harness
- M1373 must keep actor inputs and checkpoint parameters unchanged
- M1373 must produce summary, scenario, pair, intervention, accepted, reset-only, rejected, and model-fidelity artifacts
- M1373 must keep private holdout unused
- M1373 must treat accepted-row sparsity as source-sampling evidence rather than a threshold-relaxation trigger

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not mutate the candidate checkpoint
- do not claim true single-wheel, split-mu, halfshaft, or suspension physics from proxy configs
- do not claim paper-level evidence or level3 self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1373-paper-route-promoted-base-source-rich-smoke
- type: gate
- checkpoint: runs/m1373_promoted_base_source_rich_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: promoted_base_source_rich_smoke_pass_sparse_source_route_to_audit
- reason: M1373 source-rich smoke passes structurally with 832 scenarios 768 matched pairs 2 accepted rows and 174 reset-only rows

## Next Blocker

m1374-paper-route-promoted-base-source-rich-smoke-result-audit
