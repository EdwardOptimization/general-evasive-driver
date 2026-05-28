# m1249-paper-route-capability-separable-trajectory-proposal-source-design Research Review

## Summary

- Generated at UTC: 20260528T104020Z
- Type: gate
- Gate tier: process
- Promotion decision: trajectory_proposal_source_design_admit_bounded_smoke
- Decision reason: M1249 designs condition-wise no-training trajectory proposal source mining and admits bounded M1250 smoke

## Hypothesis

A condition-wise trajectory proposal source can distinguish whether zero accepted rows are due to the fixed action lattice or due to the current simulator/source state distribution.

## Lineage

- parent_checkpoint: runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt
- parent_dataset: docs/m1248-paper-route-capability-separable-fine-relocation-negative-audit.md, runs/m1247_capability_separable_fine_relocation_calibration_smoke/summary.json, runs/m1247_capability_separable_fine_relocation_calibration_smoke/relocation_candidates.csv
- parent_config: experiments/manifests/m1248-paper-route-capability-separable-fine-relocation-negative-audit.json
- parent_objective: design condition-wise trajectory proposal source mining after local relocation source exhaustion
- derived_from: m1248-paper-route-capability-separable-fine-relocation-negative-audit
- blocked_by: M1248 stops local relocation + fixed short-sequence lattice because M1242-M1247 produced zero accepted separable rows
- supersedes: another immediate local relocation-grid run, training on zero accepted source rows
- invalidates: None

## Success Criteria

- docs/m1249-paper-route-capability-separable-trajectory-proposal-source-design.md exists
- design names candidate generation strategy
- design names acceptance metrics and thresholds
- design names runtime bounds
- design names no-leak actor contract guardrails
- M1250 bounded no-training smoke manifest exists
- no training, PPO, promotion, private holdout, or actor-input expansion occurs

## Failure Criteria

- design is missing
- design feeds proposal labels or oracle outcomes into actor inputs
- design lacks acceptance gates
- training, PPO, private holdout, promotion, or actor-input expansion occurs

## Evidence Gates

- M1249 must preserve actor input contract
- M1249 must not train controllers
- M1249 must not run PPO
- M1249 must not use private holdout
- M1249 must not promote
- M1249 must define a no-training trajectory proposal/source mining protocol

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not promote
- do not add hidden parameters, proposal labels, oracle outcomes, or solver outputs to actor inputs
- do not claim self-identification from source design
- do not implement the run before pre-registering acceptance gates

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1249-paper-route-capability-separable-trajectory-proposal-source-design
- type: gate
- checkpoint: docs/m1249-paper-route-capability-separable-trajectory-proposal-source-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: trajectory_proposal_source_design_admit_bounded_smoke
- reason: M1249 designs condition-wise no-training trajectory proposal source mining and admits bounded M1250 smoke

## Next Blocker

m1250-paper-route-capability-separable-trajectory-proposal-source-smoke
