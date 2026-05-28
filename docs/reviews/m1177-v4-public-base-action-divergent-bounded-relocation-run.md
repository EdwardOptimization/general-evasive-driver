# m1177-v4-public-base-action-divergent-bounded-relocation-run Research Review

## Summary

- Generated at UTC: 20260528T022047Z
- Type: gate
- Gate tier: proof
- Promotion decision: not_applicable
- Decision reason: M1177 may only run the pre-registered bounded relocation replay over M1175 candidate_outcomes.csv and document the result. It cannot run broad mining, train actor weights, run PPO, promote, use private holdout, change actor inputs, or convert rows into a proof corpus.

## Hypothesis

M1175 action-divergent candidates will materialize into a source-diverse wrong-history boundary surface under fine target-margin bounded relocation.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m1175_action_divergent_candidate_export/candidate_outcomes.csv, docs/m1176-v4-public-base-action-divergent-bounded-relocation-design.md
- parent_config: experiments/manifests/m1176-v4-public-base-action-divergent-bounded-relocation-design.json
- parent_objective: run bounded relocation replay over action-divergent candidate_outcomes.csv
- derived_from: m1176-v4-public-base-action-divergent-bounded-relocation-design
- blocked_by: M1175 candidates have source-diverse action divergence but no direct success-drop rows
- supersedes: None
- invalidates: proof conversion from unrelocated M1175 candidates, broad relocation rerun before bounded candidate replay

## Success Criteria

- summary artifact exists
- boundary_relocation_rows.csv exists
- balanced_accepted_wrong_history_rows.csv exists
- decision is source_balanced_boundary_export_pass
- accepted_wrong_rows >= 80
- accepted_wrong_physical_pairs >= 10
- accepted_wrong_left_steps >= 5
- accepted_wrong_checkpoints >= 3
- accepted_wrong_targets >= 2
- accepted_wrong_normal_margin_buckets >= 2
- accepted_wrong_success_drop_fraction == 1.0
- max_rows_per_physical_pair_fraction <= 0.15
- control_accepted_wrong_rows == 0
- no broad mining, actor training, PPO, promotion, private holdout, conversion, or actor-input change occurs

## Failure Criteria

- summary artifact missing
- relocation runtime/resource failure
- accepted wrong-history rows remain scarce
- accepted rows collapse to old two-pair surface
- source-diversity gate fails
- broad mining, actor training, PPO, promotion, private holdout, conversion, or actor-input change starts

## Evidence Gates

- M1177 may run only the pre-registered bounded relocation command
- M1177 must not run broad mining
- M1177 must not train actor weights
- M1177 must not run PPO
- M1177 must not promote
- M1177 must not use private holdout
- M1177 must preserve actor inputs
- M1177 must not convert rows into a proof corpus

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not rerun broad mining
- do not train actor weights
- do not run PPO
- do not promote
- do not use private holdout
- do not change actor inputs
- do not convert rows into a proof corpus
- do not weaken thresholds after seeing relocation results

## Failure Taxonomy

- none

## Scoreboard

- No scoreboard row recorded.

## Next Blocker

m1177-v4-public-base-action-divergent-bounded-relocation-run
