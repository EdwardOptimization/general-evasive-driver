# m1305-paper-route-source-history-concentration-aware-refresh-design Research Review

## Summary

- Generated at UTC: 20260528T153726Z
- Type: gate
- Gate tier: process
- Promotion decision: source_history_concentration_aware_refresh_design_admit_plan_builder
- Decision reason: M1305 designs a no-training concentration-aware refresh: build pair-disjoint balanced folds and capped group weights before any weighted repeat or PPO

## Hypothesis

A concentration-aware refresh design can address M1304 source-family/probe-template concentration without overfitting to one pair ID or admitting PPO prematurely.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1304-paper-route-source-history-repeat-failed-offset-audit.md, runs/m1304_source_history_repeat_failed_offset_audit/summary.json, runs/m1304_source_history_repeat_failed_offset_audit/offset_summary.csv, runs/m1304_source_history_repeat_failed_offset_audit/failed_eval_groups.csv, runs/m1304_source_history_repeat_failed_offset_audit/composition_summary.csv
- parent_config: experiments/manifests/m1304-paper-route-source-history-repeat-failed-offset-audit.json
- parent_objective: design concentration-aware source-history corpus/objective refresh
- derived_from: m1304-paper-route-source-history-repeat-failed-offset-audit
- blocked_by: M1304 found failed-offset concentration by probe template and single-wheel grip-collapse source family
- supersedes: blind objective tuning from M1302 failed offsets
- invalidates: None

## Success Criteria

- docs/m1305-paper-route-source-history-concentration-aware-refresh-design.md exists
- design records M1304 concentration evidence
- design specifies source-family and probe-template balancing or weighting
- design specifies repeat pass/fail criteria
- design keeps PPO and promotion blocked
- no training, PPO, promotion, private holdout, threshold relaxation, or actor-input expansion occurs

## Failure Criteria

- design document is missing
- design ignores M1304 concentration evidence
- design targets a single pair ID only
- design starts training or PPO
- private holdout is used
- checkpoint is promoted
- actor input contract changes
- thresholds are relaxed after seeing results

## Evidence Gates

- M1305 must preserve actor input contract
- M1305 must not run PPO
- M1305 must not train
- M1305 must not use private holdout
- M1305 must not promote
- M1305 must specify how concentration by source family and probe template is handled
- M1305 must define pass/fail criteria for the next bounded implementation

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not train in the design milestone
- do not promote
- do not use private holdout
- do not add actor inputs
- do not relax thresholds
- do not tune only to one public failed-offset row
- do not overclaim self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1305-paper-route-source-history-concentration-aware-refresh-design
- type: gate
- checkpoint: docs/m1305-paper-route-source-history-concentration-aware-refresh-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_history_concentration_aware_refresh_design_admit_plan_builder
- reason: M1305 designs a no-training concentration-aware refresh: build pair-disjoint balanced folds and capped group weights before any weighted repeat or PPO

## Next Blocker

m1306-paper-route-source-history-concentration-refresh-plan
