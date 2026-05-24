# m751-v4-reset-source-sequence-intervention-design Research Review

## Summary

- Generated at UTC: 20260524T232330Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: v4_reset_source_sequence_intervention_design_admit_m752
- Decision reason: M751 designs source-balanced v4 sequence interventions over M749 reset-only rows with sentinel policy v4 metadata and no-training M752 implementation

## Hypothesis

M749's v4 reset-only rows can be source-balanced and tested with persistent sequence-level command-response interventions before objective work.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m750-v4-extreme-fault-coverage-audit.md, runs/m749_extreme_fault_distribution_v4/summary.json, runs/m749_extreme_fault_distribution_v4/reset_only_rows.csv, runs/m749_extreme_fault_distribution_v4/rejected_rows.csv
- parent_config: experiments/manifests/m750-v4-extreme-fault-coverage-audit.json, configs/extreme_fault_distribution_v4_scenarios.json
- parent_objective: design source-balanced sequence-level interventions over M749 v4 reset-only rows
- derived_from: m750-v4-extreme-fault-coverage-audit
- blocked_by: m750-v4-extreme-fault-coverage-audit
- supersedes: None
- invalidates: None

## Success Criteria

- M751 defines v4 source adapter fields
- M751 defines source-balance caps and sentinel policy
- M751 defines sequence variants and horizons
- M751 defines action outcome sentinel and actor-safety gates
- M751 blocks source export objective training PPO and promotion
- M751 admits only a no-training M752 implementation

## Failure Criteria

- design treats reset-only rows as wrong-history proof
- design lacks sentinel rows
- design drops v4 claim-boundary metadata
- design admits source export objective training PPO or checkpoint promotion

## Evidence Gates

- M751 designs v4 reset-source adapter and source-balance policy
- M751 includes sentinel rows from history-insensitive rejected rows
- M751 defines sequence intervention variants horizons and gates
- M751 preserves current/proxy versus future-fidelity claim boundary
- source export objective training PPO and promotion remain blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not treat reset-only rows as wrong-history proof
- do not inject hidden fault labels into actor observations
- do not train an actor
- do not run PPO
- do not promote a checkpoint
- do not claim true single-wheel physics from current proxy faults

## Failure Taxonomy

- none

## Scoreboard

- milestone: m751-v4-reset-source-sequence-intervention-design
- type: infrastructure
- checkpoint: docs/m751-v4-reset-source-sequence-intervention-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: v4_reset_source_sequence_intervention_design_admit_m752
- reason: M751 designs source-balanced v4 sequence interventions over M749 reset-only rows with sentinel policy v4 metadata and no-training M752 implementation

## Next Blocker

m752-v4-reset-source-sequence-intervention-implementation
