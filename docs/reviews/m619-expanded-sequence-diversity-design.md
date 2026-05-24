# m619-expanded-sequence-diversity-design Research Review

## Summary

- Generated at UTC: 20260524T095627Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: expanded_sequence_diversity_design_admit_m620
- Decision reason: M619 designs tier-aware sequence miner outputs and accepted candidate-set artifacts before any larger search optimizer training or PPO

## Hypothesis

M617 shows repeatable sequence signal but narrow accepted-source and action-mode diversity; the next no-training design should improve artifact provenance and candidate/source diversity before any optimizer step.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m617_expanded_sequence_target_miner/summary.json, runs/m617_expanded_sequence_target_miner/sequence_candidates.csv, runs/m617_expanded_sequence_target_miner/accepted_sequences.csv, docs/m618-expanded-sequence-target-mining-audit.md
- parent_config: experiments/manifests/m618-expanded-sequence-target-mining-audit.json, docs/m617-expanded-sequence-target-miner.md
- parent_objective: design the next no-training sequence diversity step after M617 remains diagnostic-positive but not optimizer-ready
- derived_from: m618-expanded-sequence-target-mining-audit
- blocked_by: m618-expanded-sequence-target-mining-audit
- supersedes: None
- invalidates: None

## Success Criteria

- design specifies source-tier metadata propagation into sequence miner outputs
- design specifies accepted candidate-set diversity audit
- design specifies whether to add longer low-amplitude sequence families without changing acceptance thresholds
- design keeps optimizer admission training PPO and promotion blocked
- research validation passes

## Failure Criteria

- design starts training
- design promotes a checkpoint
- design lowers target thresholds
- design widens trust regions without a separate audit
- design ignores M617 action-mode narrowness

## Evidence Gates

- define source-tier propagation requirements
- define accepted candidate-set audit requirements
- define any new sequence families without lowering trust regions
- keep target acceptance thresholds unchanged
- keep actor training and PPO blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote checkpoint
- do not lower target acceptance thresholds
- do not widen action trust regions without a separate audit
- do not treat M617 six accepted rows as optimizer-ready

## Failure Taxonomy

- none

## Scoreboard

- milestone: m619-expanded-sequence-diversity-design
- type: infrastructure
- checkpoint: docs/m619-expanded-sequence-diversity-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: expanded_sequence_diversity_design_admit_m620
- reason: M619 designs tier-aware sequence miner outputs and accepted candidate-set artifacts before any larger search optimizer training or PPO

## Next Blocker

m620-sequence-tier-aware-miner-implementation
