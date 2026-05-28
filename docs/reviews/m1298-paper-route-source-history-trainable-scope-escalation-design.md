# m1298-paper-route-source-history-trainable-scope-escalation-design Research Review

## Summary

- Generated at UTC: 20260528T145700Z
- Type: gate
- Gate tier: process
- Promotion decision: source_history_trainable_scope_design_admit_bounded_no_ppo_probe
- Decision reason: M1298 designs no-PPO fusion/head trainable-scope probe with pair-disjoint split-eval and parameter-group mutation guards; PPO and promotion remain blocked

## Hypothesis

A bounded trainable-scope diagnostic can test whether frozen decoder/fusion parameters, rather than the source corpus alone, caused actor_mean-only mixed source-history directionality.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt, runs/m1288_source_history_objective_only_update/checkpoints/raw_objective_update.pt, runs/m1295_source_history_pair_group_objective_probe/checkpoints/base_init_pair_group_candidate.pt
- parent_dataset: docs/m1297-paper-route-source-history-objective-only-update-synthesis.md, runs/m1288_source_history_objective_only_update/summary.json, runs/m1290_source_history_directional_conflict_audit/summary.json, runs/m1292_source_history_actor_mean_directional_feasibility_probe/summary.json, runs/m1295_source_history_pair_group_objective_probe/summary.json
- parent_config: experiments/manifests/m1297-paper-route-source-history-objective-only-update-synthesis.json
- parent_objective: design a bounded trainable-scope escalation diagnostic after actor_mean-only branch synthesis
- derived_from: m1297-paper-route-source-history-objective-only-update-synthesis
- blocked_by: M1297 closes actor_mean-only objective branch as underpowered
- supersedes: another actor_mean-only objective update on the same public source-history corpus
- invalidates: None

## Success Criteria

- docs/m1298-paper-route-source-history-trainable-scope-escalation-design.md exists
- design enumerates allowed trainable scopes
- design specifies source-diverse train/eval split discipline
- design specifies exact objective and directional gates
- design specifies mutation reporting by parameter group
- design blocks PPO and promotion
- no training, PPO, promotion, private holdout, threshold relaxation, or actor-input expansion occurs

## Failure Criteria

- design document is missing
- design admits PPO directly
- design changes actor inputs
- design omits split-eval discipline
- design omits mutation reporting
- design treats wider scope as self-ID proof
- training, private holdout, promotion, threshold relaxation, or actor-input expansion occurs

## Evidence Gates

- M1298 must preserve actor input contract
- M1298 must not train controllers
- M1298 must not run PPO
- M1298 must not use private holdout
- M1298 must not promote
- M1298 must define trainable parameter scopes
- M1298 must define source-diverse train/eval split discipline
- M1298 must define exact objective, directional, and mutation gates

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not train in the design milestone
- do not promote
- do not use private holdout
- do not add actor inputs
- do not allow hidden labels, source IDs, outcomes, or search metadata into actor inputs
- do not treat wider trainable scope as self-identification proof
- do not skip mutation reporting by parameter group

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1298-paper-route-source-history-trainable-scope-escalation-design
- type: gate
- checkpoint: docs/m1298-paper-route-source-history-trainable-scope-escalation-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_history_trainable_scope_design_admit_bounded_no_ppo_probe
- reason: M1298 designs no-PPO fusion/head trainable-scope probe with pair-disjoint split-eval and parameter-group mutation guards; PPO and promotion remain blocked

## Next Blocker

m1299-paper-route-source-history-trainable-scope-probe
