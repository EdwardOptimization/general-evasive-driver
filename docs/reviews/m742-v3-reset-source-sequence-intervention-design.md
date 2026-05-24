# m742-v3-reset-source-sequence-intervention-design Research Review

## Summary

- Generated at UTC: 20260524T223624Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: v3_reset_source_sequence_intervention_design_admit_m743
- Decision reason: M742 designs a source adapter source-balance sentinel policy sequence variants horizons and gates for no-training sequence interventions over M740 reset-only rows

## Hypothesis

Persistent sequence-level command-response interventions over M740 v3 reset-only rows will expose outcome-sensitive history dependence that cross-fault wrong-history swapping did not.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m741-extreme-fault-distribution-v3-audit.md, docs/m740-extreme-fault-distribution-v3-implementation.md, runs/m740_extreme_fault_distribution_v3/summary.json, runs/m740_extreme_fault_distribution_v3/reset_only_rows.csv, runs/m740_extreme_fault_distribution_v3/matched_cross_fault_pairs.csv, configs/extreme_fault_distribution_v3_scenarios.json
- parent_config: experiments/manifests/m741-extreme-fault-distribution-v3-audit.json
- parent_objective: design sequence-level command-response interventions over M740 v3 reset-only source rows
- derived_from: m741-extreme-fault-distribution-v3-audit
- blocked_by: m741-extreme-fault-distribution-v3-audit
- supersedes: None
- invalidates: None

## Success Criteria

- M742 defines source adapter and source balance rules
- M742 defines sequence intervention variants and horizons
- M742 defines sentinel action and outcome gates
- M742 blocks source export actor update PPO and promotion
- M742 admits only a no-training M743 implementation

## Failure Criteria

- design treats reset-only rows as wrong-history proof
- design changes actor input contract
- design omits sentinel false-positive checks
- design admits PPO or checkpoint promotion

## Evidence Gates

- M742 defines source adapter for M740 reset_only_rows
- M742 defines source-balance and sentinel policy
- M742 defines sequence intervention variants and horizons
- M742 separates reset action outcome and wrong-history evidence
- actor update PPO and promotion remain blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not treat reset-only rows as wrong-history proof
- do not inject hidden fault labels into actor observations
- do not train an actor
- do not run PPO
- do not promote a checkpoint
- do not claim true single-wheel physics from current single-track proxies

## Failure Taxonomy

- none

## Scoreboard

- milestone: m742-v3-reset-source-sequence-intervention-design
- type: infrastructure
- checkpoint: docs/m742-v3-reset-source-sequence-intervention-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: v3_reset_source_sequence_intervention_design_admit_m743
- reason: M742 designs a source adapter source-balance sentinel policy sequence variants horizons and gates for no-training sequence interventions over M740 reset-only rows

## Next Blocker

m743-v3-reset-source-sequence-intervention-implementation
