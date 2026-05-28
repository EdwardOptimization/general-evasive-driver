# m1182-v4-public-base-no-residual-source-rich-adapter-implementation Research Review

## Summary

- Generated at UTC: 20260528T024323Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: not_applicable
- Decision reason: M1182 may only implement no-residual source-rich adapter tooling and focused tests. It cannot run source-rich mining, run full replay, train actor weights, run PPO, promote, use private holdout, change actor inputs, or convert rows into a proof corpus.

## Hypothesis

A small no-residual adapter can reuse source-rich scenario conventions while evaluating the current public-gate actor directly and emitting the metadata needed for a later source-rich smoke run.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1181-v4-public-base-source-rich-route-compatibility-audit.md, src/autodrift/v4_low_margin_new_data_route.py, configs/cross_fault_hidden_condition_scenarios.json
- parent_config: experiments/manifests/m1181-v4-public-base-source-rich-route-compatibility-audit.json
- parent_objective: implement a no-residual source-rich adapter for current public-gate base
- derived_from: m1181-v4-public-base-source-rich-route-compatibility-audit
- blocked_by: existing source-rich tools require an incompatible residual head
- supersedes: None
- invalidates: running old residual-head routes as current-base evidence, source-rich run before no-residual adapter exists

## Success Criteria

- source module exists
- focused tests exist and pass
- adapter has no residual-head CLI requirement
- required source-rich metadata fields are emitted or validated
- follow-up smoke run manifest exists
- no mining, full replay, actor training, PPO, promotion, private holdout, conversion, or actor-input change occurs

## Failure Criteria

- adapter requires residual-head input
- actor input contract changes
- tests are missing
- implementation runs full mining or replay
- mining, actor training, PPO, promotion, private holdout, conversion, or actor-input change starts

## Evidence Gates

- M1182 may implement adapter tooling and focused tests only
- M1182 must not run source-rich mining
- M1182 must not run replay experiments beyond focused unit-level checks
- M1182 must not train actor weights
- M1182 must not run PPO
- M1182 must not promote
- M1182 must not use private holdout
- M1182 must preserve actor inputs
- M1182 must not convert rows into a proof corpus

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run source-rich mining
- do not run full replay experiments
- do not train actor weights
- do not run PPO
- do not promote
- do not use private holdout
- do not change actor inputs
- do not convert rows
- do not require residual-head inputs

## Failure Taxonomy

- none

## Scoreboard

- No scoreboard row recorded.

## Next Blocker

m1182-v4-public-base-no-residual-source-rich-adapter-implementation
