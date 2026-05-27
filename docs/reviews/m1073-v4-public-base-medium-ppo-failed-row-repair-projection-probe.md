# m1073-v4-public-base-medium-ppo-failed-row-repair-projection-probe Research Review

## Summary

- Generated at UTC: 20260527T085601Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: medium_ppo_failed_row_projection_first_replay_candidate_route_to_full_public_gate
- Decision reason: M1073 finds a no-PPO repaired projection candidate that passes exact and first replay checks using the M1072 failed-row corpus; full public gate remains pending

## Hypothesis

A no-PPO repair/projection probe using the M1072 failed-row corpus can find a candidate that restores exact and first-replay proof constraints after the M1069 medium PPO washout.

## Lineage

- parent_checkpoint: runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt, runs/ppo_m1069_expanded_gate_medium_seed61069/checkpoint.pt
- parent_dataset: docs/m1072-v4-public-base-medium-ppo-failed-row-projection-corpus-export.md, runs/m1072_medium_ppo_failed_row_projection_corpus/current_family_conflict_corpus.npz, runs/m1072_medium_ppo_failed_row_projection_corpus/failed_row_map.csv, runs/m1037_candidate_b_combined_active_set_anchor_export/combined_active_set_anchor_row16x4.npz
- parent_config: experiments/manifests/m1072-v4-public-base-medium-ppo-failed-row-projection-corpus-export.json
- parent_objective: run no-PPO exact repair/projection using the M1072 failed-row projection corpus
- derived_from: m1072-v4-public-base-medium-ppo-failed-row-projection-corpus-export
- blocked_by: M1072 exports a loadable source-labeled failed-row corpus; no projection candidate has been tested with it
- supersedes: None
- invalidates: running another PPO proposal before testing no-PPO projection, running projection with only the old M1037 anchor and not the M1072 failed-row corpus

## Success Criteria

- projection run completes
- summary artifact exists
- actor inputs are unchanged
- M1072 corpus is used
- exact candidate status is reported
- first replay status is reported
- no promotion or private holdout occurs

## Failure Criteria

- projection run crashes
- summary artifact is missing
- actor inputs change
- M1072 corpus is not used
- projection result is ambiguous
- checkpoint is promoted
- private holdout is used

## Evidence Gates

- M1073 must not run PPO
- M1073 must not promote
- M1073 must not use private holdout
- M1073 must preserve the P0 actor-input contract
- M1073 must use the M1072 failed-row projection corpus
- M1073 must gate candidates through exact/first-replay checks before any later full public gate

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not change actor inputs
- do not promote from M1073
- do not use private holdout
- do not skip M1072 corpus
- do not claim full public-gate pass from a first-replay projection probe

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1073-v4-public-base-medium-ppo-failed-row-repair-projection-probe
- type: driver_candidate
- checkpoint: runs/m1073_medium_ppo_failed_row_repair_projection_probe/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: medium_ppo_failed_row_projection_first_replay_candidate_route_to_full_public_gate
- reason: M1073 finds a no-PPO repaired projection candidate that passes exact and first replay checks using the M1072 failed-row corpus; full public gate remains pending

## Next Blocker

m1074-v4-public-base-medium-ppo-repair-projection-full-public-gate
