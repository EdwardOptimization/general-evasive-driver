# m829-v4-wrong-cross-fault-history-intervention-audit Research Review

## Summary

- Generated at UTC: 20260525T111133Z
- Type: gate
- Gate tier: process
- Promotion decision: admit_near_boundary_wrong_history_pair_mining_design
- Decision reason: M829 audits M828 as a clean wide-margin matched-pair negative and admits near-boundary wrong-history pair mining before more replay PPO or promotion

## Hypothesis

M828's negative can be attributed to hidden-only intervention being too weak, not a contract or reconstruction failure.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m828_v4_wrong_cross_fault_history_intervention/summary.json, runs/m828_v4_wrong_cross_fault_history_intervention/wrong_history_replay_rows.csv, runs/m828_v4_wrong_cross_fault_history_intervention/diversity_summary.json
- parent_config: experiments/manifests/m828-v4-wrong-cross-fault-history-intervention-implementation.json, configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json
- parent_objective: audit hidden-only wrong-cross-fault history intervention negative result
- derived_from: m828-v4-wrong-cross-fault-history-intervention-implementation
- blocked_by: M828 wrong-cross-fault hidden injection has zero accepted wrong-history rows and very small action/margin effects
- supersedes: None
- invalidates: None

## Success Criteria

- M829 writes an audit document with M828 replay metrics
- M829 verifies no actor/residual training or promotion occurred
- M829 identifies the next control variable
- M829 keeps PPO and promotion blocked

## Failure Criteria

- M829 treats closer-to-right action without margin/action threshold pass as success
- M829 admits PPO from a zero-accepted-row result
- M829 ignores reconstruction or contract issues
- M829 relaxes thresholds after seeing the result

## Evidence Gates

- M829 must inspect M828 summary and replay artifacts
- M829 must classify whether the negative is implementation, matching, or policy-insensitivity limited
- M829 must decide between full wrong-history observation replay, stronger boundary pair mining, or branch pivot
- M829 must preserve P0 actor contract and current-model/proxy boundary
- M829 must not run PPO or promote a checkpoint

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not train actor or residual parameters
- do not run PPO
- do not promote a checkpoint
- do not relax wrong-history thresholds after seeing M828
- do not treat closer-to-right action alone as pass evidence
- do not claim physical wheel-level faults from current proxies

## Failure Taxonomy

- scenario_sampling_failure
- metric_artifact
- contract_violation

## Scoreboard

- milestone: m829-v4-wrong-cross-fault-history-intervention-audit
- type: gate
- checkpoint: docs/m829-v4-wrong-cross-fault-history-intervention-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_near_boundary_wrong_history_pair_mining_design
- reason: M829 audits M828 as a clean wide-margin matched-pair negative and admits near-boundary wrong-history pair mining before more replay PPO or promotion

## Next Blocker

M828 hidden-only wrong-history intervention produced no accepted rows
