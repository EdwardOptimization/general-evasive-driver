# m667-normal-success-boundary-source-miner-implementation Research Review

## Summary

- Generated at UTC: 20260524T142938Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: normal_success_boundary_source_miner_negative_admit_audit
- Decision reason: M667 finds 204 valid near-boundary preferred windows but accepts 0 rows because wrong history creates no sustained action-sequence or outcome gap

## Hypothesis

Normal-history success and positive near-boundary margin filtering will isolate valid preferred branches before wrong-history pairing and produce usable action/outcome-critical rows.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m666-normal-success-boundary-source-mining-design.md, runs/m664_action_critical_wrong_history_source_miner/summary.json
- parent_config: experiments/manifests/m666-normal-success-boundary-source-mining-design.json
- parent_objective: implement normal-success near-boundary source miner
- derived_from: m666-normal-success-boundary-source-mining-design
- blocked_by: m666-normal-success-boundary-source-mining-design
- supersedes: None
- invalidates: None

## Success Criteria

- near_boundary_preferred left snapshots >= 40
- accepted rows >= 40
- accepted physical pairs >= 8
- accepted left seeds >= 6
- accepted right seeds >= 6
- source-heldout split is nonempty
- mean preferred_vs_rejected_action_mean_l2 >= 0.010
- mean margin_gap >= 0.010 or accepted success_drop_rate >= 0.25
- actor checksum unchanged
- no actor checkpoint written
- research validation passes

## Failure Criteria

- too few near-boundary normal-success source windows
- too few accepted rows
- normal-failed preferred branches are accepted
- source diversity fails
- actor checksum changes
- actor checkpoint is written

## Evidence Gates

- build wider obstacle decision-window snapshot bank
- run normal-history prepass and classify source windows
- pair wrong histories only for normal-success near-boundary left snapshots
- write explicit preferred/rejected NPZ fields
- verify actor checksum unchanged and no actor checkpoint written

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not update actor parameters
- do not promote checkpoint
- do not accept normal-failed preferred branches
- do not accept hidden-distance-only rows
- do not use hidden parameters or labels as actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m667-normal-success-boundary-source-miner-implementation
- type: infrastructure
- checkpoint: runs/m667_normal_success_boundary_source_miner/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: normal_success_boundary_source_miner_negative_admit_audit
- reason: M667 finds 204 valid near-boundary preferred windows but accepts 0 rows because wrong history creates no sustained action-sequence or outcome gap

## Next Blocker

m668-normal-success-boundary-source-miner-audit
