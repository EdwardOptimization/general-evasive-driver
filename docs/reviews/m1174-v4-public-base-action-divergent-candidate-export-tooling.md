# m1174-v4-public-base-action-divergent-candidate-export-tooling Research Review

## Summary

- Generated at UTC: 20260528T020355Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: not_applicable
- Decision reason: M1174 may only implement deterministic candidate export tooling and focused tests. It cannot run relocation replay, run mining, train actor weights, run PPO, promote, use private holdout, change actor inputs, or convert rows into a proof corpus.

## Hypothesis

A small deterministic exporter can create action-divergent candidate CSVs from existing outcome artifacts while preserving source-balance metadata and avoiding manual CSV editing.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1173-v4-public-base-action-divergent-candidate-export-design.md, runs/m1161_row15_promoted_margin_slack_outcome_seed116100/outcome_interventions.csv
- parent_config: experiments/manifests/m1173-v4-public-base-action-divergent-candidate-export-design.json
- parent_objective: implement a deterministic action-divergent candidate exporter for existing outcome artifacts
- derived_from: m1173-v4-public-base-action-divergent-candidate-export-design
- blocked_by: existing relocation runner does not apply action-divergence filters inline
- supersedes: None
- invalidates: manual ad hoc filtered CSVs, direct replay from unfiltered M1161 outcome CSV, proof conversion from candidate export alone

## Success Criteria

- exporter module exists
- focused tests cover filtering, scoring, source-balance caps, and summary fields
- no replay, mining, actor training, PPO, promotion, private holdout, conversion, or actor-input change occurs

## Failure Criteria

- exporter scope grows beyond candidate export
- tests are missing
- required columns are not preserved
- replay, mining, actor training, PPO, promotion, private holdout, conversion, or actor-input change starts

## Evidence Gates

- M1174 may implement exporter tooling and focused tests only
- M1174 must not run relocation replay
- M1174 must not run mining
- M1174 must not train actor weights
- M1174 must not run PPO
- M1174 must not promote
- M1174 must not use private holdout
- M1174 must preserve actor inputs
- M1174 must not convert rows into a proof corpus

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run relocation replay
- do not run mining
- do not train actor weights
- do not run PPO
- do not promote
- do not use private holdout
- do not change actor inputs
- do not convert rows into a proof corpus
- do not rely on manual CSV editing

## Failure Taxonomy

- none

## Scoreboard

- No scoreboard row recorded.

## Next Blocker

m1174-v4-public-base-action-divergent-candidate-export-tooling
