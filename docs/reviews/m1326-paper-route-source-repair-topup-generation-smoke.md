# m1326-paper-route-source-repair-topup-generation-smoke Research Review

## Summary

- Generated at UTC: 20260528T173457Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: source_repair_topup_smoke_invalid_short_horizon_route_to_horizon_corrected_smoke
- Decision reason: M1326 implements source_topup_v1 but the 9-step smoke is invalid because all rollouts terminate by horizon

## Hypothesis

The source_topup_v1 profile can improve M1323 undercovered active-family source coverage under strict no-policy source-mining thresholds.

## Lineage

- parent_checkpoint: not_applicable
- parent_dataset: docs/m1325-paper-route-source-repair-topup-generation-design.md, runs/m1323_source_repair_corpus_expansion_plan/summary.json, runs/m1322_source_repair_corpus_export/summary.json
- parent_config: experiments/manifests/m1325-paper-route-source-repair-topup-generation-design.json
- parent_objective: implement source_topup_v1 and run one no-policy top-up source-generation smoke
- derived_from: m1325-paper-route-source-repair-topup-generation-design
- blocked_by: M1325 admits one bounded top-up generation smoke before source-history materialization
- supersedes: direct materialization of the under-target M1323 corpus
- invalidates: None

## Success Criteria

- focused tests pass
- runs/m1326_source_repair_topup_generation_smoke/summary.json exists
- accepted_separable_pairs >= 240 or accepted_separable_pairs > 216 with explicit gap report
- at least two M1323 undercovered active families improve or a blocker is reported
- global friction is reported separately as accepted, diagnostic-only, missing, or source-miner mismatch
- no training, PPO, promotion, private holdout, threshold relaxation, or actor-input expansion occurs

## Failure Criteria

- focused tests fail
- run artifacts are missing
- accepted_separable_pairs <= 216 without clear blocker
- global friction is hidden or mislabeled
- strict source thresholds are relaxed
- training, PPO, private holdout, promotion, threshold relaxation, or actor-input expansion occurs

## Evidence Gates

- M1326 must not train
- M1326 must not run PPO
- M1326 must not use private holdout
- M1326 must not promote
- M1326 must preserve actor input contract
- M1326 must use strict source acceptance thresholds
- M1326 must report global friction separately

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not relax accepted thresholds
- do not fabricate global friction coverage
- do not hide undercovered family gaps
- do not claim high-fidelity tire blowout or load-transfer physics

## Failure Taxonomy

- metric_artifact
- scenario_sampling_failure

## Scoreboard

- milestone: m1326-paper-route-source-repair-topup-generation-smoke
- type: infrastructure
- checkpoint: runs/m1326_source_repair_topup_generation_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_repair_topup_smoke_invalid_short_horizon_route_to_horizon_corrected_smoke
- reason: M1326 implements source_topup_v1 but the 9-step smoke is invalid because all rollouts terminate by horizon

## Next Blocker

m1327-paper-route-source-repair-topup-horizon-corrected-smoke
