# m446-policy-difference-miner-implementation Research Review

## Summary

- Generated at UTC: 20260523T192700Z
- Type: infrastructure
- Gate tier: generalization
- Promotion decision: admit_m447_fresh_policy_difference_mining_run
- Decision reason: M446 implements policy-difference miner and smoke finds only two return-delta rows with no outcome or margin divergence

## Hypothesis

A reusable policy-difference miner can turn broad benchmark episodes into source-diverse candidate rows for the next generalization surface.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m444_proof_utility_generalization_seed9600/episodes.csv
- parent_config: experiments/manifests/m445-fresh-policy-difference-miner-design.json
- parent_objective: policy-difference miner implementation
- derived_from: m445-fresh-policy-difference-miner-design
- blocked_by: m445-fresh-policy-difference-miner-design
- supersedes: None
- invalidates: None

## Success Criteria

- CLI reads benchmark episodes CSV and baseline policy
- CLI exports accepted and compact policy-difference CSVs
- CLI exports summary JSON with diversity counts
- smoke run on M444 episodes completes
- focused tests pass

## Failure Criteria

- miner cannot handle no accepted rows
- miner requires hidden/oracle actor inputs
- miner promotes or trains a checkpoint
- summary omits diversity accounting

## Evidence Gates

- policy-difference miner smoke runs on M444 episodes
- candidate and compact CSV artifacts written
- summary JSON written
- focused tests pass

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not change actor input/output contract
- do not make policy labels actor inputs
- do not treat M444 as private holdout

## Failure Taxonomy

- none

## Scoreboard

- milestone: m446-policy-difference-miner-implementation
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m447_fresh_policy_difference_mining_run
- reason: M446 implements policy-difference miner and smoke finds only two return-delta rows with no outcome or margin divergence

## Next Blocker

m447-fresh-policy-difference-mining-run
