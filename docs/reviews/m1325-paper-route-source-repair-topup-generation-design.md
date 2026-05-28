# m1325-paper-route-source-repair-topup-generation-design Research Review

## Summary

- Generated at UTC: 20260528T172455Z
- Type: gate
- Gate tier: process
- Promotion decision: source_repair_topup_generation_design_admit_no_policy_smoke
- Decision reason: M1325 designs source_topup_v1 for undercovered halfshaft load brake and blowout-like families while keeping global friction separate

## Hypothesis

A bounded targeted top-up source-generation design can address M1323 undercovered source families without hiding global friction or changing the actor contract.

## Lineage

- parent_checkpoint: not_applicable
- parent_dataset: docs/m1324-paper-route-source-repair-corpus-plan-result-audit.md, runs/m1323_source_repair_corpus_expansion_plan/summary.json, runs/m1323_source_repair_corpus_expansion_plan/requires_source_generator_update.csv
- parent_config: experiments/manifests/m1324-paper-route-source-repair-corpus-plan-result-audit.json
- parent_objective: design targeted top-up source generation after M1324 synthesis
- derived_from: m1324-paper-route-source-repair-corpus-plan-result-audit
- blocked_by: M1324 closes the corpus expansion branch and opens top-up generation because M1323 remains below pair-count targets
- supersedes: direct source-history materialization from the under-target M1323 plan
- invalidates: None

## Success Criteria

- docs/m1325-paper-route-source-repair-topup-generation-design.md exists
- design targets halfshaft, load/CG, brake asymmetry, and tire-blowout-like undercoverage
- design keeps global friction separate from split-mu and tire-blowout-like families
- design specifies a no-policy top-up smoke route
- design preserves strict source acceptance thresholds
- no training, PPO, promotion, private holdout, threshold relaxation, or actor-input expansion occurs

## Failure Criteria

- design document is missing
- design hides global friction gap
- design relabels existing families as global friction
- design routes directly to materialization or PPO
- training, PPO, private holdout, promotion, threshold relaxation, or actor-input expansion occurs

## Evidence Gates

- M1325 must not train
- M1325 must not run PPO
- M1325 must not use private holdout
- M1325 must not promote
- M1325 must preserve actor input contract
- M1325 must target undercovered source families explicitly
- M1325 must keep global friction as a separate blocker or diagnostic source path

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not fabricate global friction coverage
- do not relabel split-mu or blowout rows as global friction
- do not route to source-history materialization before top-up coverage is audited
- do not overclaim self-identification

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m1325-paper-route-source-repair-topup-generation-design
- type: gate
- checkpoint: docs/m1325-paper-route-source-repair-topup-generation-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_repair_topup_generation_design_admit_no_policy_smoke
- reason: M1325 designs source_topup_v1 for undercovered halfshaft load brake and blowout-like families while keeping global friction separate

## Next Blocker

m1326-paper-route-source-repair-topup-generation-smoke
