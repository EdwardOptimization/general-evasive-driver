# m750-v4-extreme-fault-coverage-audit Research Review

## Summary

- Generated at UTC: 20260524T232037Z
- Type: gate
- Gate tier: process
- Promotion decision: promote_to_v4_reset_source_sequence_intervention
- Decision reason: M750 audits M749 as broad reset-only v4 evidence and selects source-balanced v4 sequence interventions before objective PPO or four-wheel fidelity branch

## Hypothesis

M749's v4 wave should be audited as reset-only source evidence, and if clean should promote to v4 reset-source sequence intervention rather than objective training.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m749-v4-extreme-fault-coverage-implementation.md, runs/m749_extreme_fault_distribution_v4/summary.json, runs/m749_extreme_fault_distribution_v4/reset_only_rows.csv, runs/m749_extreme_fault_distribution_v4/rejected_rows.csv, runs/m749_extreme_fault_distribution_v4/fault_family_summary.csv, runs/m749_extreme_fault_distribution_v4/fault_family_pair_summary.csv
- parent_config: experiments/manifests/m749-v4-extreme-fault-coverage-implementation.json, configs/extreme_fault_distribution_v4_scenarios.json
- parent_objective: audit v4 extreme-fault source-mining wave before sequence intervention or objective work
- derived_from: m749-v4-extreme-fault-coverage-implementation
- blocked_by: m749-v4-extreme-fault-coverage-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- M750 records M749 source generation metrics
- M750 records reset-only and wrong-history evidence separately
- M750 records source diversity and concentration
- M750 records supported and falsified claims
- M750 records next branch decision
- actor update PPO and promotion remain blocked unless later designed

## Failure Criteria

- audit treats reset-only rows as wrong-history proof
- audit ignores future-fidelity claim boundary
- audit admits PPO or promotion directly
- audit changes actor input contract

## Evidence Gates

- M749 source generation and reset-surface gates are audited
- M749 wrong-history zero-result is classified separately from reset evidence
- M749 future-fidelity claim boundary is audited
- next branch decision compares v4 sequence intervention four-wheel fidelity and objective work
- actor training PPO and promotion remain blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not treat reset-only rows as wrong-history proof
- do not claim proxy faults are true per-wheel physics
- do not train an actor
- do not run PPO
- do not promote a checkpoint
- do not change actor input contract

## Failure Taxonomy

- scenario_sampling_failure
- metric_artifact

## Scoreboard

- milestone: m750-v4-extreme-fault-coverage-audit
- type: gate
- checkpoint: docs/m750-v4-extreme-fault-coverage-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: promote_to_v4_reset_source_sequence_intervention
- reason: M750 audits M749 as broad reset-only v4 evidence and selects source-balanced v4 sequence interventions before objective PPO or four-wheel fidelity branch

## Next Blocker

m751-v4-reset-source-sequence-intervention-design
