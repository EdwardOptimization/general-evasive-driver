# m1369-paper-route-public-base-promotion-generalization-gate-implementation Research Review

## Summary

- Generated at UTC: 20260528T210804Z
- Type: gate
- Gate tier: promotion
- Promotion decision: public_base_promotion_generalization_gate_candidate_route_to_promotion_audit
- Decision reason: M1369 passes exact proof source-diverse fresh OOD and behavior tiers and classifies M1362 alpha 0.1 as a promotion-audit candidate

## Hypothesis

The M1362 alpha 0.1 checkpoint can pass a no-training public-base promotion/generalization gate against M1154 after its broad public replay pass.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt, runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: docs/m1368-paper-route-public-base-promotion-generalization-design.md, runs/m1365_bidirectional_broader_public_replay/summary.json, runs/m1362_bidirectional_active_set_interpolation_preflight/alpha_summary.csv, runs/m1336_materialized_source_history_objective_corpus_export
- parent_config: experiments/manifests/m1368-paper-route-public-base-promotion-generalization-design.json, configs/m121_human_view_zero_obstacle_relvel.json, configs/eval_m574_moderate_ood_l3.json
- parent_objective: run the no-training public-base promotion/generalization gate for M1362 alpha 0.1
- derived_from: m1368-paper-route-public-base-promotion-generalization-design
- blocked_by: M1368 defines the gate criteria; M1362 alpha 0.1 has broad public replay evidence but no fresh generalization gate
- supersedes: direct promotion after M1365, direct PPO after M1365, private holdout before public promotion gate, candidate-b hardcoded promotion gate reuse without generic labels
- invalidates: None

## Success Criteria

- summary artifact exists
- exact source-history retention is evaluated
- public proof replay and source-diverse diagnostics are evaluated
- fresh public and moderate-OOD generalization are evaluated
- behavior and ablation retention seeds are evaluated
- result class and failure taxonomy are written
- no training, PPO, private holdout, promotion, threshold relaxation, actor update, or actor-input expansion occurs

## Failure Criteria

- actor input contract changes
- exact source-history retention fails
- public proof replay or source-diverse diagnostics fail
- fresh public or moderate-OOD generalization regresses
- behavior or ablation retention regresses
- training, PPO, private holdout, promotion, threshold relaxation, actor update, or actor-input expansion occurs

## Evidence Gates

- M1369 must keep actor inputs unchanged
- M1369 must evaluate exact source-history retention
- M1369 must run six public proof replay surfaces or consume a clearly matching recomputed wrapper
- M1369 must evaluate source-diverse protected diagnostics
- M1369 must run fresh public and moderate-OOD generalization comparisons
- M1369 must run behavior and ablation retention seeds
- M1369 must not train, run PPO, use private holdout, or promote

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not update actor weights
- do not promote
- do not use private holdout
- do not add actor inputs
- do not relax thresholds after seeing failures
- do not let a single legacy protected key veto a source-diverse pass
- do not claim strong self-identification or paper-level source-rich extreme validation

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1369-paper-route-public-base-promotion-generalization-gate-implementation
- type: gate
- checkpoint: runs/m1369_public_base_promotion_generalization_gate/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: public_base_promotion_generalization_gate_candidate_route_to_promotion_audit
- reason: M1369 passes exact proof source-diverse fresh OOD and behavior tiers and classifies M1362 alpha 0.1 as a promotion-audit candidate

## Next Blocker

m1370-paper-route-public-base-promotion-audit
