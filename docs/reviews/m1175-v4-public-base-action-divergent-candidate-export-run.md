# m1175-v4-public-base-action-divergent-candidate-export-run Research Review

## Summary

- Generated at UTC: 20260528T021022Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: not_applicable
- Decision reason: M1175 may only run the candidate exporter and document the export. It cannot run relocation replay, run mining, train actor weights, run PPO, promote, use private holdout, change actor inputs, or convert rows into a proof corpus.

## Hypothesis

The M1174 exporter will produce a source-diverse action-divergent candidate CSV from M1161 outcome rows under the M1173 gates.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1174-v4-public-base-action-divergent-candidate-export-tooling.md, runs/m1161_row15_promoted_margin_slack_outcome_seed116100/outcome_interventions.csv
- parent_config: experiments/manifests/m1174-v4-public-base-action-divergent-candidate-export-tooling.json
- parent_objective: run the action-divergent candidate exporter on the M1161 outcome artifacts
- derived_from: m1174-v4-public-base-action-divergent-candidate-export-tooling
- blocked_by: M1174 implements exporter tooling and focused tests
- supersedes: None
- invalidates: manual candidate CSV creation, relocation replay before candidate export audit, proof conversion from unverified export

## Success Criteria

- summary artifact exists
- candidate_outcomes.csv exists
- selection decision is action_divergent_candidates_ready
- selected rows are reported
- selected physical pairs >= 12
- selected targets >= 3
- selected checkpoints >= 6
- selected left steps >= 6
- max selected pair fraction <= 0.15
- no replay, mining, actor training, PPO, promotion, private holdout, conversion, or actor-input change occurs

## Failure Criteria

- summary artifact is missing
- candidate_outcomes.csv is missing
- source diversity gate fails
- export collapses to old two-pair surface
- replay, mining, actor training, PPO, promotion, private holdout, conversion, or actor-input change starts

## Evidence Gates

- M1175 may run only the M1174 exporter command
- M1175 must not run relocation replay
- M1175 must not run mining
- M1175 must not train actor weights
- M1175 must not run PPO
- M1175 must not promote
- M1175 must not use private holdout
- M1175 must preserve actor inputs
- M1175 must not convert rows into a proof corpus

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
- do not manually edit candidate CSVs

## Failure Taxonomy

- none

## Scoreboard

- No scoreboard row recorded.

## Next Blocker

m1175-v4-public-base-action-divergent-candidate-export-run
