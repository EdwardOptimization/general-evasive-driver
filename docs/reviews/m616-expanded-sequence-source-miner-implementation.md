# m616-expanded-sequence-source-miner-implementation Research Review

## Summary

- Generated at UTC: 20260524T094135Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: expanded_sequence_source_miner_pass_admit_m617
- Decision reason: M616 expands M609 rollout-backed source rows to 30 tiered rows with 27 physical pairs 15 left seeds 2 surfaces 2 variants and diversity_pass true while keeping training PPO and promotion blocked

## Hypothesis

Expanding M609 source rollouts into core near and support boundary tiers can provide a source-diverse table for a repeat sequence target miner without changing model weights or target acceptance thresholds.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m609_boundary_conditioned_source_miner/source_rollouts.csv, runs/m609_boundary_conditioned_source_miner/boundary_source_rows.csv, runs/m613_sequence_target_miner/accepted_sequences.csv, docs/m615-sequence-source-expansion-design.md
- parent_config: experiments/manifests/m615-sequence-source-expansion-design.json, docs/m614-sequence-target-mining-audit.md
- parent_objective: implement expanded sequence-source miner before repeating sequence target mining
- derived_from: m615-sequence-source-expansion-design
- blocked_by: m615-sequence-source-expansion-design
- supersedes: None
- invalidates: None

## Success Criteria

- expanded source rows cover at least 24 rows
- expanded source rows cover at least 16 physical pairs and 10 left seeds
- expanded source rows cover at least 2 surfaces 2 variants and 2 targets
- max physical-pair dominance is at most 0.20
- summary records actor_parameters_changed false ppo_used false promoted false optimizer_admission false
- focused tests and research validation pass

## Failure Criteria

- implementation trains a model
- implementation runs PPO
- implementation promotes a checkpoint
- implementation lowers sequence target acceptance thresholds
- implementation drops hidden provenance fields
- implementation adds unsupported history variants

## Evidence Gates

- write expanded_sequence_source_rows.csv
- write rejected_sequence_source_rows.csv
- write summary.json with source-tier diversity
- preserve deterministic hidden provenance
- keep target acceptance thresholds unchanged
- keep actor training and PPO blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote checkpoint
- do not change actor inputs
- do not lower M613 target acceptance thresholds
- do not add shuffled or neighbor history rows without deterministic provenance

## Failure Taxonomy

- none

## Scoreboard

- milestone: m616-expanded-sequence-source-miner-implementation
- type: infrastructure
- checkpoint: runs/m616_expanded_sequence_source_miner/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: expanded_sequence_source_miner_pass_admit_m617
- reason: M616 expands M609 rollout-backed source rows to 30 tiered rows with 27 physical pairs 15 left seeds 2 surfaces 2 variants and diversity_pass true while keeping training PPO and promotion blocked

## Next Blocker

m617-expanded-sequence-target-miner
