# m1217-paper-route-current-family-matched-current-export Research Review

## Summary

- Generated at UTC: 20260528T070346Z
- Type: gate
- Gate tier: proof
- Promotion decision: current_family_matched_current_surface_pass_admit_action_screen
- Decision reason: M1217 exports a source-diverse current-family M1212 L3 matched-current surface with 1790 accepted pairs 427 physical pairs 4 probe seeds 21 left steps 12 obstacle buckets and 3 targets and admits M1218 action screening

## Hypothesis

The current corrected M1212 L3 checkpoint family exposes a source-diverse matched-current ambiguity surface suitable for later causal history intervention gates.

## Lineage

- parent_checkpoint: runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111600/checkpoint.pt, runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111601/checkpoint.pt, runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt
- parent_dataset: docs/m1216-paper-route-causal-history-source-audit.md, docs/m1215-paper-route-causal-history-gate-design.md
- parent_config: configs/paper_route_corrected_profiles/m1207_l3_online_gru.json, experiments/manifests/m1216-paper-route-causal-history-source-audit.json
- parent_objective: export a fresh matched-current ambiguity surface for the current corrected L3 family
- derived_from: m1216-paper-route-causal-history-source-audit
- blocked_by: M1216 selects current-family matched-current export before any history-intervention action screen
- supersedes: directly reusing old M503 or BC5660 surfaces as the first current paper-route causal gate
- invalidates: treating old matched-current surfaces as automatically compatible with M1212 corrected L3 checkpoints

## Success Criteria

- runs/m1217_current_family_matched_current_export/summary.json exists
- runs/m1217_current_family_matched_current_export/matched_pairs.csv exists
- runs/m1217_current_family_matched_current_export/candidate_pairs.csv exists
- accepted pairs >= 120
- accepted physical pairs >= 30
- probe seeds >= 3
- left steps >= 5
- obstacle buckets >= 4
- targets >= 2
- private holdout remains unused
- no action intervention, outcome intervention, training, PPO, promotion, private holdout, profile tuning, or actor-input contract expansion occurs
- next action-screen or fallback expansion milestone is selected

## Failure Criteria

- M1217 trains or tunes profiles
- private holdout is used
- action or outcome interventions are run
- surface is source-narrow
- self-identification is claimed from pair mining

## Evidence Gates

- M1217 may run matched-current pair mining only
- M1217 must use P0 human-view no-wheel no-oracle corrected L3 checkpoints
- M1217 must write matched_pairs candidate_pairs target_summary and summary artifacts
- M1217 must not run action interventions
- M1217 must not run outcome interventions
- M1217 must not train controllers
- M1217 must not run PPO
- M1217 must not use private holdout
- M1217 must not promote
- M1217 must not claim self-identification

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run action or outcome intervention gates
- do not use private holdout
- do not promote
- do not tune profiles
- do not use hidden or oracle actor inputs
- do not claim history necessity from pair mining alone

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1217-paper-route-current-family-matched-current-export
- type: gate
- checkpoint: runs/m1217_current_family_matched_current_export/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: current_family_matched_current_surface_pass_admit_action_screen
- reason: M1217 exports a source-diverse current-family M1212 L3 matched-current surface with 1790 accepted pairs 427 physical pairs 4 probe seeds 21 left steps 12 obstacle buckets and 3 targets and admits M1218 action screening

## Next Blocker

m1218-paper-route-current-family-history-action-screen
