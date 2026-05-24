# m610-boundary-conditioned-grounded-target-miner Research Review

## Summary

- Generated at UTC: 20260524T090403Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: boundary_conditioned_target_miner_negative_admit_sequence_audit
- Decision reason: M610 runs diagnostic target search on 17 M609 boundary rows and still accepts 0 first-action targets; max trust-region improvement is 0.015549 so training remains blocked

## Hypothesis

Restricting grounded action target search to M609 near-boundary source rows will produce stronger simulator margin/risk improvements than the broad M606 belief-only source selection.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m609_boundary_conditioned_source_miner/boundary_source_rows.csv, runs/m609_boundary_conditioned_source_miner/summary.json
- parent_config: experiments/manifests/m609-boundary-conditioned-source-miner-implementation.json, docs/m609-boundary-conditioned-source-miner-implementation.md
- parent_objective: run limited no-training grounded target search on boundary-conditioned M609 source rows
- derived_from: m609-boundary-conditioned-source-miner-implementation
- blocked_by: m609-boundary-conditioned-source-miner-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- target_candidates.csv is written
- accepted_targets.csv is written
- unaccepted_rows.csv is written
- target_corpus.npz is written when accepted targets exist
- summary records diagnostic_only true actor_parameters_changed false ppo_used false promoted false
- research validation and focused tests pass

## Failure Criteria

- miner trains any model
- miner uses private holdout rows
- miner omits unaccepted rows
- miner writes privileged actor inputs
- miner promotes a checkpoint
- miner claims optimizer admission from the 17-row source set

## Evidence Gates

- read M609 boundary_source_rows.csv
- write target candidate rollouts
- write accepted target rows
- write unaccepted rows
- treat accepted targets as diagnostic only unless diversity is later expanded
- prove no model weights are changed

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote checkpoint
- do not treat M609's 17-row source set as sufficient optimizer corpus
- do not lower M606 acceptance thresholds retroactively
- do not add privileged actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m610-boundary-conditioned-grounded-target-miner
- type: infrastructure
- checkpoint: runs/m610_boundary_conditioned_grounded_target_miner/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: boundary_conditioned_target_miner_negative_admit_sequence_audit
- reason: M610 runs diagnostic target search on 17 M609 boundary rows and still accepts 0 first-action targets; max trust-region improvement is 0.015549 so training remains blocked

## Next Blocker

m611-boundary-target-mining-audit
