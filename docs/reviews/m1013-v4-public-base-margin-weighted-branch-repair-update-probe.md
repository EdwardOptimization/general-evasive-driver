# m1013-v4-public-base-margin-weighted-branch-repair-update-probe Research Review

## Summary

- Generated at UTC: 20260526T185645Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: margin_weighted_branch_repair_update_branch_trust_blocked_route_to_audit
- Decision reason: M1013 finds 10 exact temporal candidates but 0 exact plus branch-trust candidates; failure is proof_washout and next route is failure audit before threshold changes

## Hypothesis

The M1012 actor_mean-only repair objective can produce at least one exact temporal candidate that stays inside the M1011 margin-weighted wrong-branch trust region.

## Lineage

- parent_checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
- parent_dataset: docs/m1012-v4-public-base-margin-weighted-branch-repair-update-design.md, runs/m997_v4_public_base_temporal_sequence_corpus_export/temporal_sequence_corpus.npz, runs/m1011_v4_public_base_margin_weighted_branch_trust_region_evaluator/summary.json, runs/m1011_v4_public_base_margin_weighted_branch_trust_region_evaluator/branch_margin_inputs.csv
- parent_config: experiments/manifests/m1012-v4-public-base-margin-weighted-branch-repair-update-design.json
- parent_objective: implement actor_mean-only temporal repair update with M1011 margin-weighted branch trust residual
- derived_from: m1012-v4-public-base-margin-weighted-branch-repair-update-design
- blocked_by: M1012 design must be implemented before any M267/M264 replay preflight
- supersedes: None
- invalidates: direct replay or PPO from M1002 temporal candidates

## Success Criteria

- summary.json exists
- only actor_mean parameters change
- at least one candidate passes exact temporal gates
- at least one exact candidate passes M1011 branch trust gates
- ppo_used == false
- promoted == false

## Failure Criteria

- non-actor_mean parameters change
- all candidates fail exact temporal gates
- all exact candidates fail M1011 branch trust gates
- PPO starts
- promotion occurs

## Evidence Gates

- M1013 may update only actor_mean
- M1013 must not run PPO
- M1013 must not promote
- M1013 must preserve P0 actor inputs
- M1013 must gate candidates with exact temporal and M1011 branch-trust metrics before replay

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train recurrent or encoder parameters
- do not use private holdout
- do not run full replay before exact/trust candidate selection
- do not change actor input contract
- do not relax branch trust thresholds inside the same milestone

## Failure Taxonomy

- proof_washout

## Scoreboard

- milestone: m1013-v4-public-base-margin-weighted-branch-repair-update-probe
- type: infrastructure
- checkpoint: runs/m1013_v4_public_base_margin_weighted_branch_repair_update_probe/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: margin_weighted_branch_repair_update_branch_trust_blocked_route_to_audit
- reason: M1013 finds 10 exact temporal candidates but 0 exact plus branch-trust candidates; failure is proof_washout and next route is failure audit before threshold changes

## Next Blocker

m1014-v4-public-base-margin-weighted-repair-failure-audit
