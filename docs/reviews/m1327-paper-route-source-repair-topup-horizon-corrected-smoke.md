# m1327-paper-route-source-repair-topup-horizon-corrected-smoke Research Review

## Summary

- Generated at UTC: 20260528T174553Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: source_topup_horizon_corrected_mixed_route_to_additive_merge_audit
- Decision reason: M1327 reruns source_topup_v1 with 72-step horizon and gets 150 accepted rows source-positive but under target as standalone corpus

## Hypothesis

The source_topup_v1 profile must be judged with sequence_length=72 before concluding whether it improves M1323 undercovered source-family coverage.

## Lineage

- parent_checkpoint: not_applicable
- parent_dataset: docs/m1326-paper-route-source-repair-topup-generation-smoke.md, runs/m1326_source_repair_topup_generation_smoke/summary.json
- parent_config: experiments/manifests/m1326-paper-route-source-repair-topup-generation-smoke.json
- parent_objective: rerun source_topup_v1 with the historical 72-step source horizon after M1326 invalid short-horizon result
- derived_from: m1326-paper-route-source-repair-topup-generation-smoke
- blocked_by: M1326 used sequence_length=9 and all rollouts terminated by horizon
- supersedes: using the M1326 9-step result for source-family conclusions
- invalidates: M1326 zero-acceptance result as a source-family separability conclusion

## Success Criteria

- runs/m1327_source_repair_topup_horizon_corrected_smoke/summary.json exists
- sequence_length == 72
- terminal_reason_counts is not all horizon
- accepted_separable_pairs >= 240 or accepted_separable_pairs > 216 with explicit gap report
- global friction is reported separately as accepted, diagnostic-only, missing, or source-miner mismatch
- no training, PPO, promotion, private holdout, threshold relaxation, or actor-input expansion occurs

## Failure Criteria

- run artifacts are missing
- sequence_length != 72
- terminal_reason_counts is still all horizon
- accepted_separable_pairs <= 216 without clear blocker
- global friction is hidden or mislabeled
- strict source thresholds are relaxed
- training, PPO, private holdout, promotion, threshold relaxation, or actor-input expansion occurs

## Evidence Gates

- M1327 must not train
- M1327 must not run PPO
- M1327 must not use private holdout
- M1327 must not promote
- M1327 must preserve actor input contract
- M1327 must use strict source acceptance thresholds
- M1327 must use sequence_length=72
- M1327 must report global friction separately

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
- do not reuse the M1326 9-step result as valid source evidence
- do not claim high-fidelity tire blowout or load-transfer physics

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1327-paper-route-source-repair-topup-horizon-corrected-smoke
- type: infrastructure
- checkpoint: runs/m1327_source_repair_topup_horizon_corrected_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_topup_horizon_corrected_mixed_route_to_additive_merge_audit
- reason: M1327 reruns source_topup_v1 with 72-step horizon and gets 150 accepted rows source-positive but under target as standalone corpus

## Next Blocker

m1328-paper-route-source-topup-additive-merge-audit
