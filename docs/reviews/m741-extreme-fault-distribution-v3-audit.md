# m741-extreme-fault-distribution-v3-audit Research Review

## Summary

- Generated at UTC: 20260524T223129Z
- Type: gate
- Gate tier: process
- Promotion decision: promote_to_v3_reset_source_sequence_intervention
- Decision reason: M741 audits M740 as broad reset-only evidence and selects source-balanced sequence-level intervention over v3 reset rows before simulator fidelity or PPO

## Hypothesis

M740's broad v3 reset-only source surface should be audited before deciding whether to run sequence-level interventions or change simulator fidelity.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m740-extreme-fault-distribution-v3-implementation.md, runs/m740_extreme_fault_distribution_v3/summary.json, runs/m740_extreme_fault_distribution_v3/reset_only_rows.csv, runs/m740_extreme_fault_distribution_v3/matched_cross_fault_pairs.csv, runs/m740_extreme_fault_distribution_v3/rejected_rows.csv
- parent_config: experiments/manifests/m740-extreme-fault-distribution-v3-implementation.json, configs/extreme_fault_distribution_v3_scenarios.json
- parent_objective: audit v3 extreme-fault data wave reset-only result before sequence intervention or fidelity branch
- derived_from: m740-extreme-fault-distribution-v3-implementation
- blocked_by: m740-extreme-fault-distribution-v3-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- M741 records M740 source generation evidence
- M741 records reset-only versus wrong-history evidence
- M741 records supported and falsified claims
- M741 records public gate overfit risk
- M741 makes an explicit next branch decision
- actor update PPO and promotion remain blocked unless later designed

## Failure Criteria

- audit treats reset-only rows as wrong-history proof
- audit ignores model-fidelity boundary
- audit admits PPO or promotion directly
- audit changes actor input contract

## Evidence Gates

- M740 source generation and diversity are audited
- M740 reset-only result is separated from wrong-history evidence
- model-fidelity boundary is checked
- next branch decision compares v3 sequence-level intervention simulator fidelity and objective work
- actor training PPO and promotion remain blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not treat reset-only rows as wrong-history proof
- do not train an actor
- do not run PPO
- do not promote a checkpoint
- do not claim true single-wheel physics from current single-track proxies
- do not change actor input contract

## Failure Taxonomy

- scenario_sampling_failure
- metric_artifact

## Scoreboard

- milestone: m741-extreme-fault-distribution-v3-audit
- type: gate
- checkpoint: docs/m741-extreme-fault-distribution-v3-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: promote_to_v3_reset_source_sequence_intervention
- reason: M741 audits M740 as broad reset-only evidence and selects source-balanced sequence-level intervention over v3 reset rows before simulator fidelity or PPO

## Next Blocker

m742-v3-reset-source-sequence-intervention-design
