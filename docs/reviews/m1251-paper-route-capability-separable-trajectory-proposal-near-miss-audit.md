# m1251-paper-route-capability-separable-trajectory-proposal-near-miss-audit Research Review

## Summary

- Generated at UTC: 20260528T105212Z
- Type: gate
- Gate tier: process
- Promotion decision: trajectory_proposal_near_miss_admit_targeted_margin_restoration_smoke
- Decision reason: M1251 audits M1250 pair 5 near-miss and admits one targeted margin-restoration smoke without threshold relaxation

## Hypothesis

M1250's two-sided regret but slightly nonviable row is actionable source evidence, but requires audit before another repair or pivot.

## Lineage

- parent_checkpoint: runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt
- parent_dataset: docs/m1250-paper-route-capability-separable-trajectory-proposal-source-smoke.md, runs/m1250_capability_separable_trajectory_proposal_source_smoke/summary.json, runs/m1250_capability_separable_trajectory_proposal_source_smoke/matched_capability_pairs.csv, runs/m1250_capability_separable_trajectory_proposal_source_smoke/relocation_candidates.csv
- parent_config: experiments/manifests/m1250-paper-route-capability-separable-trajectory-proposal-source-smoke.json
- parent_objective: audit trajectory proposal near-miss source result before changing thresholds or running another source smoke
- derived_from: m1250-paper-route-capability-separable-trajectory-proposal-source-smoke
- blocked_by: M1250 produced zero accepted source rows but found a two-sided regret row whose own-branch margins were only slightly negative
- supersedes: lowering acceptance thresholds after seeing M1250, starting training before accepted source rows exist
- invalidates: None

## Success Criteria

- docs/m1251-paper-route-capability-separable-trajectory-proposal-near-miss-audit.md exists
- audit cites M1250 pair 5 near-miss metrics
- audit does not lower source-positive thresholds
- audit chooses targeted repair or pivot
- no training, PPO, promotion, private holdout, or actor-input expansion occurs

## Failure Criteria

- audit is missing
- audit ignores M1250 near-miss evidence
- audit lowers acceptance thresholds
- training, PPO, private holdout, promotion, or actor-input expansion occurs

## Evidence Gates

- M1251 must preserve actor input contract
- M1251 must not train controllers
- M1251 must not run PPO
- M1251 must not use private holdout
- M1251 must not promote
- M1251 must decide whether the M1250 near-miss justifies one targeted source repair or a branch pivot

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not promote
- do not add hidden parameters, proposal labels, oracle outcomes, or search outputs to actor inputs
- do not lower source-positive thresholds after seeing M1250
- do not claim self-identification from near-miss source evidence

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m1251-paper-route-capability-separable-trajectory-proposal-near-miss-audit
- type: gate
- checkpoint: docs/m1251-paper-route-capability-separable-trajectory-proposal-near-miss-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: trajectory_proposal_near_miss_admit_targeted_margin_restoration_smoke
- reason: M1251 audits M1250 pair 5 near-miss and admits one targeted margin-restoration smoke without threshold relaxation

## Next Blocker

m1252-paper-route-capability-separable-proposal-margin-restoration-smoke
