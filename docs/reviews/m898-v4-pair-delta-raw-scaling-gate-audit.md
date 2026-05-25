# m898-v4-pair-delta-raw-scaling-gate-audit Research Review

## Summary

- Generated at UTC: 20260525T202300Z
- Type: gate
- Gate tier: process
- Promotion decision: raw_scaling_gate_audit_route_to_fresh_generalization_design
- Decision reason: M898 audits raw scaling as proof-safe larger movement and routes to fresh generalization design before PPO promotion or integration

## Hypothesis

M897 raw candidates are proof-safe and larger than alpha_0_1, but they need an audit before any fresh/generalization test, integration design, or PPO.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt, runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/raw_candidate.pt, runs/m891_v4_enriched_pair_delta_objective_only_repeat_seed10887/checkpoints/raw_candidate.pt
- parent_dataset: docs/m897-v4-pair-delta-raw-candidate-controlled-scaling-gate.md, runs/m897_m886_raw_exact_recheck/summary.json, runs/m897_m891_raw_exact_recheck/summary.json, runs/m897_raw_controlled_scaling_first_replay_gate/summary.json, runs/m897_raw_controlled_scaling_full_replay_gate/summary.json, runs/m897_raw_controlled_scaling_behavior_seed9505/policy_summary.csv, runs/m897_raw_controlled_scaling_behavior_seed9506/policy_summary.csv
- parent_config: experiments/manifests/m897-v4-pair-delta-raw-candidate-controlled-scaling-gate.json
- parent_objective: audit raw-candidate controlled scaling gate and choose fresh/generalization, boundary-search, integration, or corpus-routing
- derived_from: m897-v4-pair-delta-raw-candidate-controlled-scaling-gate
- blocked_by: M897 passed raw-candidate public proof gates but has not been audited for next-route implications
- supersedes: None
- invalidates: None

## Success Criteria

- M898 records M897 exact, replay, and behavior results
- M898 compares raw movement with alpha_0_1
- M898 states supported and unsupported claims
- M898 chooses the next route
- M898 keeps PPO and promotion blocked

## Failure Criteria

- M898 promotes raw candidates
- M898 admits PPO
- M898 claims generalization from public gates
- M898 omits effect-size caveats
- M898 skips routing

## Evidence Gates

- M898 must separate proof-safe raw scaling from driver improvement
- M898 must compare raw effect size against alpha_0_1
- M898 must decide the next route without PPO or promotion
- M898 must record public-gate overfit limitations
- M898 must keep actor input contract unchanged

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not train actor or residual parameters
- do not run PPO
- do not promote a checkpoint
- do not claim generalization from public proof gates
- do not route directly to public-base integration without a separate design milestone

## Failure Taxonomy

- objective_overfit
- metric_artifact
- behavior_regression
- proof_washout
- contract_violation
- lineage_invalid

## Scoreboard

- milestone: m898-v4-pair-delta-raw-scaling-gate-audit
- type: gate
- checkpoint: docs/m898-v4-pair-delta-raw-scaling-gate-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: raw_scaling_gate_audit_route_to_fresh_generalization_design
- reason: M898 audits raw scaling as proof-safe larger movement and routes to fresh generalization design before PPO promotion or integration

## Next Blocker

Raw-candidate controlled scaling pass has not yet been audited for next-route selection
