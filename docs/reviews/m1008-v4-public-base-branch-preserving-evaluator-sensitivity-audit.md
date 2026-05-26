# m1008-v4-public-base-branch-preserving-evaluator-sensitivity-audit Research Review

## Summary

- Generated at UTC: 20260526T180705Z
- Type: gate
- Gate tier: process
- Promotion decision: branch_preserving_evaluator_sensitivity_audit_route_to_temporal_objective_branch_synthesis
- Decision reason: M1008 audits M1007 as margin-slack mismatch: near-zero wrong margins make tiny alpha 0.01 action shifts flip rows 6 and 15 while fixed one-step proxy stays zero; cadence requires synthesis next

## Hypothesis

M1007 fails because fixed one-step logp/separation metrics are weakly coupled to closed-loop terminal margin on near-boundary wrong-history rows.

## Lineage

- parent_checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt, runs/m1002_v4_public_base_temporal_sequence_objective_update_probe/checkpoints/alpha_0_01.pt, runs/m1002_v4_public_base_temporal_sequence_objective_update_probe/checkpoints/alpha_0_2.pt
- parent_dataset: docs/m1007-v4-public-base-branch-preserving-temporal-repair-evaluator.md, runs/m1007_v4_public_base_branch_preserving_temporal_repair_evaluator/summary.json, runs/m1007_v4_public_base_branch_preserving_temporal_repair_evaluator/branch_metric_rows.csv, runs/m1004_v4_public_base_temporal_sequence_update_public_replay_gate/candidate_preflight_summary.csv
- parent_config: experiments/manifests/m1007-v4-public-base-branch-preserving-temporal-repair-evaluator.json
- parent_objective: audit why fixed one-step branch-ceiling and branch-separation terms are insensitive to M1004 proof washout
- derived_from: m1007-v4-public-base-branch-preserving-temporal-repair-evaluator
- blocked_by: M1007 branch proxy is finite and base-safe but does not activate for alpha 0.01 proof washout
- supersedes: None
- invalidates: actor update using the M1007 fixed one-step branch proxy

## Success Criteria

- audit document exists
- M1007 proxy metrics and M1004 closed-loop margins are compared
- failure is classified with process-v2 taxonomy
- next residual design or branch synthesis route is registered

## Failure Criteria

- audit ignores M1004 row-level replay evidence
- audit routes to actor update with the failed M1007 proxy
- audit routes to PPO
- audit uses private holdout

## Evidence Gates

- M1008 must not train
- M1008 must not run PPO
- M1008 must not promote
- M1008 must compare M1007 proxy metrics against M1004 closed-loop proof washout
- M1008 must decide whether to design a margin-aware or trajectory-aware residual

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not tune the failed M1007 proxy into an actor update
- do not use private holdout
- do not claim branch preservation from fixed one-step metrics
- do not run PPO

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1008-v4-public-base-branch-preserving-evaluator-sensitivity-audit
- type: gate
- checkpoint: docs/m1008-v4-public-base-branch-preserving-evaluator-sensitivity-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: branch_preserving_evaluator_sensitivity_audit_route_to_temporal_objective_branch_synthesis
- reason: M1008 audits M1007 as margin-slack mismatch: near-zero wrong margins make tiny alpha 0.01 action shifts flip rows 6 and 15 while fixed one-step proxy stays zero; cadence requires synthesis next

## Next Blocker

m1009-v4-public-base-temporal-sequence-objective-branch-synthesis
