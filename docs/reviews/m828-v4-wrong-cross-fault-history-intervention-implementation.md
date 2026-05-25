# m828-v4-wrong-cross-fault-history-intervention-implementation Research Review

## Summary

- Generated at UTC: 20260525T110602Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: v4_wrong_cross_fault_history_intervention_history_insensitive
- Decision reason: M828 implements wrong-cross-fault hidden injection across 108 reconstructed pairs; all wrong-hidden actions move closer to right action but effects are below action and margin thresholds so zero accepted rows and PPO remains blocked

## Hypothesis

Injecting recurrent history from a matched different hidden-dynamics source will expose stronger response-history self-ID evidence than reset or zero-command ablations alone.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m825_v4_extreme_hidden_dynamics_data_route/matched_pair_rows.csv, runs/m825_v4_extreme_hidden_dynamics_data_route/candidate_plan_rows.csv, runs/m825_v4_extreme_hidden_dynamics_data_route/source_rows.csv, docs/m827-v4-wrong-cross-fault-history-intervention-design.md
- parent_config: experiments/manifests/m827-v4-wrong-cross-fault-history-intervention-design.json, configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json
- parent_objective: implement no-training wrong-cross-fault history intervention replay
- derived_from: m827-v4-wrong-cross-fault-history-intervention-design
- blocked_by: wrong-cross-fault history intervention is designed but not implemented
- supersedes: None
- invalidates: None

## Success Criteria

- M828 writes implementation and run artifacts
- M828 evaluates normal, reset, zero-command, shifted/delayed, and wrong-cross-fault history variants
- M828 reports wrong-history margin/action degradation separately from zero-command sensitivity
- M828 confirms actor and residual-head checksums unchanged
- M828 keeps PPO and promotion blocked

## Failure Criteria

- M828 trains actor or residual parameters
- M828 runs PPO
- M828 promotes a checkpoint
- M828 uses hidden fault labels as actor inputs
- M828 treats diagnostic matched action divergence as replay evidence without wrong-history rollout

## Evidence Gates

- M828 must implement no-training wrong-cross-fault history replay
- M828 must preserve actor and residual-head checksums
- M828 must not feed fault labels or hidden params to actor input
- M828 must report accepted wrong-history and mitigation row counts
- M828 must report zero-command dominance separately
- M828 must not run PPO or promote a checkpoint

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not train actor or residual parameters
- do not run PPO
- do not promote a checkpoint
- do not use fault labels as actor inputs
- do not count zero-command-only rows as wrong-history proof
- do not claim physical wheel-level faults from current proxies

## Failure Taxonomy

- scenario_sampling_failure
- metric_artifact
- contract_violation

## Scoreboard

- milestone: m828-v4-wrong-cross-fault-history-intervention-implementation
- type: infrastructure
- checkpoint: runs/m828_v4_wrong_cross_fault_history_intervention/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: v4_wrong_cross_fault_history_intervention_history_insensitive
- reason: M828 implements wrong-cross-fault hidden injection across 108 reconstructed pairs; all wrong-hidden actions move closer to right action but effects are below action and margin thresholds so zero accepted rows and PPO remains blocked

## Next Blocker

wrong-cross-fault history evidence is not yet measured
