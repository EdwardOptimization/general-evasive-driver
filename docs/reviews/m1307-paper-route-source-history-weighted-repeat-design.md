# m1307-paper-route-source-history-weighted-repeat-design Research Review

## Summary

- Generated at UTC: 20260528T154719Z
- Type: gate
- Gate tier: process
- Promotion decision: source_history_weighted_repeat_design_route_to_branch_synthesis
- Decision reason: M1307 designs a bounded weighted repeat protocol from the M1306 plan and requires branch synthesis before implementation or PPO

## Hypothesis

The M1306 admissible plan can be converted into a bounded no-PPO weighted fusion_head repeat protocol with clear pass/fail gates and synthesis before implementation.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1306-paper-route-source-history-concentration-refresh-plan.md, runs/m1306_source_history_concentration_refresh_plan/summary.json, runs/m1306_source_history_concentration_refresh_plan/balanced_split_rows.csv, runs/m1306_source_history_concentration_refresh_plan/group_weight_rows.csv, runs/m1306_source_history_concentration_refresh_plan/fold_composition_summary.csv
- parent_config: experiments/manifests/m1306-paper-route-source-history-concentration-refresh-plan.json
- parent_objective: design bounded weighted trainable-scope repeat using M1306 plan
- derived_from: m1306-paper-route-source-history-concentration-refresh-plan
- blocked_by: M1306 produced an admissible plan but no weighted repeat protocol exists
- supersedes: direct weighted trainable-scope implementation without process design
- invalidates: None

## Success Criteria

- docs/m1307-paper-route-source-history-weighted-repeat-design.md exists
- design specifies split-plan usage
- design specifies group-weight usage and caps
- design specifies pass/fail criteria
- design requires branch synthesis before implementation or PPO
- design keeps PPO and promotion blocked
- no training, PPO, promotion, private holdout, threshold relaxation, pair-specific weighting, or actor-input expansion occurs

## Failure Criteria

- design document is missing
- design omits split-plan or group-weight usage
- design starts training or PPO
- design permits pair-specific weights
- private holdout is used
- checkpoint is promoted
- actor input contract changes
- thresholds are relaxed after seeing results

## Evidence Gates

- M1307 must preserve actor input contract
- M1307 must not run PPO
- M1307 must not train
- M1307 must not use private holdout
- M1307 must not promote
- M1307 must define how split-plan and group weights enter the next probe
- M1307 must require branch synthesis before any larger training or PPO step

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not train in the design milestone
- do not promote
- do not use private holdout
- do not add actor inputs
- do not relax thresholds
- do not use pair_id-specific weights
- do not overclaim self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1307-paper-route-source-history-weighted-repeat-design
- type: gate
- checkpoint: docs/m1307-paper-route-source-history-weighted-repeat-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_history_weighted_repeat_design_route_to_branch_synthesis
- reason: M1307 designs a bounded weighted repeat protocol from the M1306 plan and requires branch synthesis before implementation or PPO

## Next Blocker

m1308-paper-route-source-history-trainable-scope-escalation-synthesis
