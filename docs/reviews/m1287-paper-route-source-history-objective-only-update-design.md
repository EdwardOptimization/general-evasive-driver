# m1287-paper-route-source-history-objective-only-update-design Research Review

## Summary

- Generated at UTC: 20260528T140216Z
- Type: gate
- Gate tier: process
- Promotion decision: source_history_objective_only_update_design_admit_tiny_actor_mean_implementation
- Decision reason: M1287 designs exact-loss-first actor_mean_only no-PPO update path and admits bounded M1288 implementation

## Hypothesis

A bounded no-PPO objective-only update can be designed around the exact M1285 source-history residual with strict retention guardrails.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1286-paper-route-four-wheel-source-intervention-materialization-synthesis.md, runs/m1285_source_history_objective_evaluator/summary.json, runs/m1285_source_history_objective_evaluator/source_history_objective_rows.csv
- parent_config: experiments/manifests/m1286-paper-route-four-wheel-source-intervention-materialization-synthesis.json
- parent_objective: design a no-PPO objective-only update around the exact M1285 source-history residual
- derived_from: m1286-paper-route-four-wheel-source-intervention-materialization-synthesis
- blocked_by: M1286 promotes to the source-history objective-only update branch
- supersedes: continuing source-intervention materialization branch after synthesis
- invalidates: None

## Success Criteria

- docs/m1287-paper-route-source-history-objective-only-update-design.md exists
- design specifies trainable scopes
- design specifies exact M1285 loss gate
- design specifies retention and no-PPO guardrails
- design admits at most a tiny no-PPO implementation
- no training, PPO, promotion, private holdout, threshold relaxation, or actor-input expansion occurs

## Failure Criteria

- design document is missing
- design starts PPO directly
- design omits exact M1285 loss gate
- design omits retention guardrails
- design overclaims self-identification
- training, PPO, private holdout, promotion, threshold relaxation, or actor-input expansion occurs

## Evidence Gates

- M1287 must preserve actor input contract
- M1287 must not train controllers
- M1287 must not run PPO
- M1287 must not use private holdout
- M1287 must not promote
- M1287 must design objective-only update stages and retention gates
- M1287 must keep exact M1285 objective as the first gate

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not promote
- do not add actor inputs
- do not skip exact M1285 loss gate
- do not run public replay gates before exact-loss sanity
- do not overclaim self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1287-paper-route-source-history-objective-only-update-design
- type: gate
- checkpoint: docs/m1287-paper-route-source-history-objective-only-update-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_history_objective_only_update_design_admit_tiny_actor_mean_implementation
- reason: M1287 designs exact-loss-first actor_mean_only no-PPO update path and admits bounded M1288 implementation

## Next Blocker

m1288-paper-route-source-history-objective-only-update-implementation
