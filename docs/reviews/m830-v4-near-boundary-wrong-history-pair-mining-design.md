# m830-v4-near-boundary-wrong-history-pair-mining-design Research Review

## Summary

- Generated at UTC: 20260525T112457Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: near_boundary_wrong_history_pair_mining_design_ready_synthesis_required
- Decision reason: M830 designs boundary-first matched different-fault pair mining with near-boundary normal-margin bands wrong-history separation and diversity gates while routing to branch synthesis before implementation due cadence

## Hypothesis

Near-boundary matched different-fault pairs will expose stronger wrong-history margin sensitivity than the wide-margin M828 pair set.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m828_v4_wrong_cross_fault_history_intervention/wrong_history_replay_rows.csv, docs/m829-v4-wrong-cross-fault-history-intervention-audit.md
- parent_config: experiments/manifests/m829-v4-wrong-cross-fault-history-intervention-audit.json, configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json
- parent_objective: design near-boundary matched wrong-history pair mining after M828 wide-margin negative
- derived_from: m829-v4-wrong-cross-fault-history-intervention-audit
- blocked_by: M828 matched pairs had normal margins >=0.217m and zero accepted wrong-history rows
- supersedes: None
- invalidates: None

## Success Criteria

- M830 writes a design document for near-boundary wrong-history pair mining
- M830 defines required implementation artifacts and pass/fail gates
- M830 specifies how to avoid public-row overfitting and zero-command dominance
- M830 keeps PPO and promotion blocked

## Failure Criteria

- M830 proposes threshold relaxation instead of new boundary-aware data
- M830 admits PPO without wrong-history evidence
- M830 ignores M828 wide-margin diagnosis
- M830 violates the P0 actor input contract

## Evidence Gates

- M830 must design matched pair mining with explicit near-boundary normal-margin constraints
- M830 must keep wrong-history evidence separate from zero-command evidence
- M830 must define source/fault/warm-up/onset diversity gates
- M830 must preserve P0 actor contract and current-model/proxy boundary
- M830 must keep PPO and promotion blocked

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not train actor or residual parameters
- do not run PPO
- do not promote a checkpoint
- do not relax M828 thresholds after seeing the result
- do not count wide-margin action-divergent pairs as boundary proof
- do not feed fault labels or hidden params to actor

## Failure Taxonomy

- scenario_sampling_failure
- metric_artifact
- contract_violation

## Scoreboard

- milestone: m830-v4-near-boundary-wrong-history-pair-mining-design
- type: infrastructure
- checkpoint: docs/m830-v4-near-boundary-wrong-history-pair-mining-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: near_boundary_wrong_history_pair_mining_design_ready_synthesis_required
- reason: M830 designs boundary-first matched different-fault pair mining with near-boundary normal-margin bands wrong-history separation and diversity gates while routing to branch synthesis before implementation due cadence

## Next Blocker

near-boundary matched wrong-history pair source does not yet exist
