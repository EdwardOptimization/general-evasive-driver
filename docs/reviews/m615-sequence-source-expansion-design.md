# m615-sequence-source-expansion-design Research Review

## Summary

- Generated at UTC: 20260524T093039Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: sequence_source_expansion_design_admit_m616
- Decision reason: M615 designs source expansion through core near and support boundary tiers from M609 source rollouts while keeping sequence acceptance thresholds training PPO and promotion blocked

## Hypothesis

M613 sequence-target signal is real but too narrow; expanding boundary source diversity before repeating sequence mining may produce enough accepted sequences for a later objective design.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m609_boundary_conditioned_source_miner/boundary_source_rows.csv, runs/m613_sequence_target_miner/accepted_sequences.csv, docs/m614-sequence-target-mining-audit.md
- parent_config: experiments/manifests/m614-sequence-target-mining-audit.json, docs/m612-sequence-target-mining-design.md
- parent_objective: design source expansion before repeating sequence target mining
- derived_from: m614-sequence-target-mining-audit
- blocked_by: m614-sequence-target-mining-audit
- supersedes: None
- invalidates: None

## Success Criteria

- design specifies expanded source rows and boundary windows
- design specifies deterministic provenance for any new history variants
- design specifies minimum accepted-sequence diversity for later objective admission
- design keeps training and PPO blocked
- research validation passes

## Failure Criteria

- design starts training
- design lowers target acceptance thresholds
- design permits optimizer admission from one accepted row
- design uses privileged actor inputs
- design promotes a checkpoint

## Evidence Gates

- define expanded source-screen policy
- define deterministic hidden provenance requirements
- define sequence-mining repeat thresholds
- keep target acceptance thresholds unchanged
- keep actor training and PPO blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train in design milestone
- do not run PPO
- do not promote checkpoint
- do not lower target acceptance thresholds
- do not treat one accepted M613 sequence as sufficient corpus
- do not add privileged actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m615-sequence-source-expansion-design
- type: infrastructure
- checkpoint: docs/m615-sequence-source-expansion-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: sequence_source_expansion_design_admit_m616
- reason: M615 designs source expansion through core near and support boundary tiers from M609 source rollouts while keeping sequence acceptance thresholds training PPO and promotion blocked

## Next Blocker

m616-expanded-sequence-source-miner-implementation
