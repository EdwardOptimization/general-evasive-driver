# m612-sequence-target-mining-design Research Review

## Summary

- Generated at UTC: 20260524T090904Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: sequence_target_mining_design_admit_m613
- Decision reason: M612 designs diagnostic K=3/5 structured action-sequence target mining with unchanged margin/risk thresholds and keeps PPO training and promotion blocked

## Hypothesis

M610 failed because single first-action overrides are too myopic; a short bounded action-sequence target miner may discover simulator-grounded maneuver targets on the same near-boundary rows.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m609_boundary_conditioned_source_miner/boundary_source_rows.csv, runs/m610_boundary_conditioned_grounded_target_miner/summary.json, docs/m611-boundary-target-mining-audit.md
- parent_config: experiments/manifests/m611-boundary-target-mining-audit.json, docs/m610-boundary-conditioned-grounded-target-miner.md
- parent_objective: design short-horizon sequence target mining after first-action locality blocker
- derived_from: m611-boundary-target-mining-audit
- blocked_by: m611-boundary-target-mining-audit
- supersedes: None
- invalidates: None

## Success Criteria

- design specifies sequence length and candidate families
- design specifies per-step and sequence trust regions
- design specifies no-collision margin/risk acceptance criteria
- design specifies artifacts for accepted and unaccepted sequence candidates
- research validation passes

## Failure Criteria

- design starts training
- design runs PPO
- design promotes a checkpoint
- design drops unaccepted row logging
- design creates actor inputs from privileged labels

## Evidence Gates

- define sequence candidate families
- define sequence trust region
- define sequence acceptance thresholds
- define diagnostic-only target corpus fields
- keep actor training and PPO blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train in design milestone
- do not run PPO
- do not promote checkpoint
- do not reinterpret M610 first-action failures as accepted
- do not add privileged actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m612-sequence-target-mining-design
- type: infrastructure
- checkpoint: docs/m612-sequence-target-mining-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: sequence_target_mining_design_admit_m613
- reason: M612 designs diagnostic K=3/5 structured action-sequence target mining with unchanged margin/risk thresholds and keeps PPO training and promotion blocked

## Next Blocker

m613-sequence-target-miner-implementation
