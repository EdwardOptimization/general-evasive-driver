# m1164-v4-public-base-row15-promoted-relocation-expansion-run Research Review

## Summary

- Generated at UTC: 20260528T011321Z
- Type: gate
- Gate tier: proof
- Promotion decision: row15_promoted_relocation_expansion_resource_failure_route_to_staged_design
- Decision reason: M1164 was interrupted after roughly 33 minutes with no summary artifact so it provides a resource-scope failure and routes to staged relocation design

## Hypothesis

Bounded body-frame relocation expansion over existing M1161 outcomes can recover a source-diverse wrong-history margin-slack surface without weakening acceptance thresholds.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1163-v4-public-base-row15-promoted-relocation-expansion-design.md, runs/m1161_row15_promoted_margin_slack_outcome_seed116100/outcome_interventions.csv
- parent_config: experiments/manifests/m1163-v4-public-base-row15-promoted-relocation-expansion-design.json
- parent_objective: run bounded relocation expansion over M1161 outcome rows without rerunning mining or weakening thresholds
- derived_from: m1163-v4-public-base-row15-promoted-relocation-expansion-design
- blocked_by: M1163 designs the bounded relocation-expansion diagnostic
- supersedes: None
- invalidates: objective conversion before relocation expansion result, PPO before relocation expansion result, new mining before isolating relocation width

## Success Criteria

- summary artifact exists
- source_budget_ready == true
- accepted_wrong_history_rows >= 100
- accepted_wrong_physical_pairs >= 12
- accepted_wrong_left_steps >= 6
- accepted_wrong_checkpoints >= 4
- accepted_wrong_targets >= 2
- accepted_wrong_normal_margin_buckets >= 3 at width 0.005
- accepted_wrong_normal_margin_max >= 0.01
- accepted_wrong_success_drop_fraction == 1.0
- max_rows_per_physical_pair_fraction <= 0.25
- control_accepted_wrong_rows == 0
- no actor training, PPO, promotion, private holdout, mining rerun, outcome rerun, or actor-input change occurs

## Failure Criteria

- summary artifact is missing
- source_budget_ready is false
- accepted wrong-history rows remain sparse
- accepted wrong-history rows remain duplicate dominated
- accepted wrong-history normal-margin max remains below 0.01
- thresholds are weakened
- actor training, PPO, promotion, private holdout, mining rerun, outcome rerun, or actor-input change starts

## Evidence Gates

- M1164 may run only the M1163 relocation-expansion command
- M1164 must reuse the existing M1161 outcome CSV
- M1164 must not rerun matched-current mining
- M1164 must not rerun the matched-history outcome gate
- M1164 must preserve M1160 acceptance thresholds
- M1164 must not train actor weights
- M1164 must not run PPO
- M1164 must not promote
- M1164 must not use private holdout
- M1164 must preserve actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not rerun mining
- do not rerun outcome gate
- do not train actor weights
- do not run PPO
- do not promote
- do not use private holdout
- do not change actor inputs
- do not weaken M1160 acceptance thresholds
- do not convert the surface in this milestone

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m1164-v4-public-base-row15-promoted-relocation-expansion-run
- type: gate
- checkpoint: docs/m1164-v4-public-base-row15-promoted-relocation-expansion-run.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: row15_promoted_relocation_expansion_resource_failure_route_to_staged_design
- reason: M1164 was interrupted after roughly 33 minutes with no summary artifact so it provides a resource-scope failure and routes to staged relocation design

## Next Blocker

m1165-v4-public-base-row15-promoted-staged-relocation-expansion-design
