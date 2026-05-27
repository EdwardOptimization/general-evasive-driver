# m1072-v4-public-base-medium-ppo-failed-row-projection-corpus-export Research Review

## Summary

- Generated at UTC: 20260527T082319Z
- Type: objective_sanity
- Gate tier: proof
- Promotion decision: medium_ppo_failed_row_projection_corpus_pass_route_to_projection_probe
- Decision reason: M1072 exports 22 source-labeled failed rows across eight proof surfaces into a loadable projection corpus without PPO or actor optimization

## Hypothesis

M1069 failed rows can be exported into a source-labeled projection corpus that preserves old public, M1061 family-intersection, and source-diverse proof constraints without training.

## Lineage

- parent_checkpoint: runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt, runs/ppo_m1069_expanded_gate_medium_seed61069/checkpoint.pt
- parent_dataset: docs/m1071-v4-public-base-medium-ppo-repair-projection-design.md, runs/m1069_expanded_gate_medium_ppo_seed61069/proof_replay_summary.csv, runs/m1069_expanded_gate_medium_ppo_seed61069/raw_candidate_gate/family_intersection_public_gate/replay_gate_summary.csv, runs/m1069_expanded_gate_medium_ppo_seed61069/raw_candidate_gate/source_diverse_protected_diagnostic/replay_gate_summary.csv
- parent_config: experiments/manifests/m1071-v4-public-base-medium-ppo-repair-projection-design.json
- parent_objective: export a source-labeled M1069 failed-row projection corpus before any repair optimizer
- derived_from: m1071-v4-public-base-medium-ppo-repair-projection-design
- blocked_by: M1071 requires a combined source-diverse failed-row corpus before projection can be tested
- supersedes: None
- invalidates: running repair/projection with only the old M1037 row15/row16 anchor, collapsing M1061 family-intersection source rows into one unlabeled corpus

## Success Criteria

- summary artifact exists
- failed-row map CSV exists
- old public failed rows are represented
- M1061 family-intersection failed rows are represented
- source-diverse failed rows are represented
- source labels and source checkpoints are preserved
- exported tensors load under the P0 actor contract
- no PPO actor training promotion or private holdout occurs

## Failure Criteria

- summary artifact is missing
- failed rows cannot be matched to source corpora
- M1061 failed rows are omitted
- source labels are missing
- exported tensors fail loader validation
- PPO or actor training starts
- private holdout is used

## Evidence Gates

- M1072 must not run PPO
- M1072 must not train actor
- M1072 must not promote
- M1072 must not use private holdout
- M1072 must export or validate source-labeled failed rows from old public replay, M1061 family-intersection, and source-diverse surfaces
- M1072 must validate that exported tensors load under the P0 actor contract

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not optimize actor weights
- do not promote
- do not use private holdout
- do not drop M1061 failed rows
- do not merge source-policy rows without source labels

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1072-v4-public-base-medium-ppo-failed-row-projection-corpus-export
- type: objective_sanity
- checkpoint: runs/m1072_medium_ppo_failed_row_projection_corpus/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: medium_ppo_failed_row_projection_corpus_pass_route_to_projection_probe
- reason: M1072 exports 22 source-labeled failed rows across eight proof surfaces into a loadable projection corpus without PPO or actor optimization

## Next Blocker

m1073-v4-public-base-medium-ppo-failed-row-repair-projection-probe
