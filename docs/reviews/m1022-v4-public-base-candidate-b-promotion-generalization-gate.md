# m1022-v4-public-base-candidate-b-promotion-generalization-gate Research Review

## Summary

- Generated at UTC: 20260526T203039Z
- Type: gate
- Gate tier: promotion
- Promotion decision: candidate_b_promotion_gate_candidate_route_to_promotion_audit
- Decision reason: M1022 classifies Candidate B as a promotion-audit candidate after exact retention proof replay source-diverse fresh public moderate-OOD and behavior tiers pass without promotion

## Hypothesis

Candidate B can pass a no-training promotion/generalization gate against the M974 public base after passing M1019 full public replay.

## Lineage

- parent_checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt, runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt
- parent_dataset: docs/m1021-v4-public-base-candidate-b-promotion-generalization-design.md, runs/m1019_v4_public_base_m1013_candidate_b_full_replay_gate/summary.json, runs/m997_v4_public_base_temporal_sequence_corpus_export/temporal_sequence_corpus.npz
- parent_config: configs/m121_human_view_zero_obstacle_relvel.json, configs/eval_m574_moderate_ood_l3.json, experiments/manifests/m1021-v4-public-base-candidate-b-promotion-generalization-design.json
- parent_objective: run Candidate B promotion/generalization gate without promotion
- derived_from: m1021-v4-public-base-candidate-b-promotion-generalization-design
- blocked_by: Candidate B has public replay evidence but has not passed fresh promotion/generalization checks
- supersedes: None
- invalidates: None

## Success Criteria

- summary artifact exists
- exact temporal retention is recomputed
- proof replay and source-diverse diagnostics are evaluated
- fresh public and moderate-OOD generalization are evaluated
- behavior/ablation seeds are evaluated
- no promotion, PPO, private holdout, or actor-input change occurs

## Failure Criteria

- exact retention fails
- proof replay fails
- fresh public or moderate-OOD generalization regresses
- behavior retention fails
- the gate promotes Candidate B or uses private holdout

## Evidence Gates

- M1022 must recompute exact temporal retention
- M1022 must run proof replay and source-diverse diagnostics
- M1022 must run fresh public and moderate-OOD generalization evals
- M1022 must run behavior and ablation retention seeds
- M1022 must not train, run PPO, use private holdout, or promote

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not use private holdout
- do not promote Candidate B
- do not change actor inputs
- do not skip exact retention
- do not skip fresh public generalization
- do not tune thresholds after seeing failures

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1022-v4-public-base-candidate-b-promotion-generalization-gate
- type: gate
- checkpoint: runs/m1022_v4_public_base_candidate_b_promotion_generalization_gate/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: candidate_b_promotion_gate_candidate_route_to_promotion_audit
- reason: M1022 classifies Candidate B as a promotion-audit candidate after exact retention proof replay source-diverse fresh public moderate-OOD and behavior tiers pass without promotion

## Next Blocker

m1023-v4-public-base-candidate-b-promotion-audit
