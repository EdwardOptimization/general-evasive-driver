# m1036-v4-public-base-candidate-b-combined-active-set-repair-design Research Review

## Summary

- Generated at UTC: 20260526T235308Z
- Type: gate
- Gate tier: proof
- Promotion decision: candidate_b_combined_active_set_repair_design_admit_combined_anchor_export
- Decision reason: M1036 designs source-namespaced family-normalized combined active-set anchors before repair and routes to no-update combined anchor export

## Hypothesis

A combined active-set repair/projection design can preserve M997 temporal retention, M297/M270 exact no-regression, M267/M264 row15, and M183/M170 row16 before first replay.

## Lineage

- parent_checkpoint: runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt, runs/ppo_m1026_candidate_b_guarded_smoke_seed61026/checkpoint.pt
- parent_dataset: docs/m1035-v4-public-base-candidate-b-guarded-ppo-readiness-synthesis.md, runs/m1034_candidate_b_m183_row16_active_set_anchor_export/m183_row16_normal_trajectory_anchor.npz, runs/m293_current_family_rejected_history_ppo_repair_design/m267_failed_rows_extra4_anchor.npz, runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz, runs/m393_current_family_rejected_boundary_targets/current_family_conflict_corpus.npz, runs/m997_v4_public_base_temporal_sequence_corpus_export/temporal_sequence_corpus.npz
- parent_config: experiments/manifests/m1035-v4-public-base-candidate-b-guarded-ppo-readiness-synthesis.json
- parent_objective: design combined active-set repair/projection using M293 plus M1034 trajectory anchors
- derived_from: m1035-v4-public-base-candidate-b-guarded-ppo-readiness-synthesis
- blocked_by: M1035 promotes the Candidate B guarded PPO readiness branch to combined active-set repair
- supersedes: None
- invalidates: rerunning M1029 repair without M183/M170 row16 active-set anchor, running longer PPO before combined active-set repair is designed, promoting M1031 or M1034 artifacts

## Success Criteria

- design artifact exists
- combined anchor or multi-anchor strategy is specified
- gate order includes M997, M297/M270, M267/M264 row15, and M183/M170 row16
- next implementation scope is bounded
- no PPO repair promotion private holdout or actor-input change occurs

## Failure Criteria

- design omits any hard active-set component
- design relaxes M997 thresholds
- design runs repair or PPO
- design changes actor inputs
- design promotes a candidate

## Evidence Gates

- M1036 must run no PPO
- M1036 must not run repair or promote
- M1036 must not use private holdout
- M1036 must preserve P0 actor inputs
- M1036 must specify how M293 and M1034 anchors are combined and gated before replay

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not run exact repair from the design milestone
- do not promote
- do not drop M997 temporal retention
- do not drop M267/M264 row15
- do not drop M183/M170 row16
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1036-v4-public-base-candidate-b-combined-active-set-repair-design
- type: gate
- checkpoint: docs/m1036-v4-public-base-candidate-b-combined-active-set-repair-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: candidate_b_combined_active_set_repair_design_admit_combined_anchor_export
- reason: M1036 designs source-namespaced family-normalized combined active-set anchors before repair and routes to no-update combined anchor export

## Next Blocker

m1037-v4-public-base-candidate-b-combined-active-set-anchor-export
