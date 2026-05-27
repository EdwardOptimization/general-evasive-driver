# m1038-v4-public-base-candidate-b-combined-active-set-repair-projection-probe Research Review

## Summary

- Generated at UTC: 20260527T004405Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: candidate_b_combined_active_set_projection_first_replay_candidate_route_to_full_public_gate_design
- Decision reason: M1038 selects base_row16x4 alpha0.15 as a first-replay candidate passing M997 M297/M270 M267/M264 row15 and M183/M170 row16 with no PPO promotion or private holdout

## Hypothesis

A no-PPO exact repair/projection using the row16x4 combined active-set anchor can retain M297/M270 exact objectives, M997 temporal retention, M267/M264 row15, and M183/M170 row16 before any full public gate.

## Lineage

- parent_checkpoint: runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt, runs/ppo_m1026_candidate_b_guarded_smoke_seed61026/checkpoint.pt
- parent_dataset: docs/m1037-v4-public-base-candidate-b-combined-active-set-anchor-export.md, runs/m1037_candidate_b_combined_active_set_anchor_export/combined_active_set_anchor_row16x4.npz, runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz, runs/m393_current_family_rejected_boundary_targets/current_family_conflict_corpus.npz, runs/m997_v4_public_base_temporal_sequence_corpus_export/temporal_sequence_corpus.npz
- parent_config: experiments/manifests/m1037-v4-public-base-candidate-b-combined-active-set-anchor-export.json
- parent_objective: run no-PPO exact repair/projection using the row16x4 combined active-set anchor
- derived_from: m1037-v4-public-base-candidate-b-combined-active-set-anchor-export
- blocked_by: M1037 provides a loadable row16x4 combined active-set anchor but no repaired/projection candidate has been tested
- supersedes: None
- invalidates: running repair with the pre-M1037 M293-only trajectory anchor, running longer PPO before combined active-set repair/projection

## Success Criteria

- summary json exists
- actor inputs unchanged
- no PPO promotion private holdout occurs
- M297/M270 exact no-regression is reported
- combined active-set anchor losses are reported
- M997 temporal exact retention is reported before replay
- M267/M264 first replay row15 status is reported for eligible candidates
- M183/M170 first replay row16 status is reported for eligible candidates

## Failure Criteria

- repair/projection cannot run
- actor inputs change
- PPO or private holdout is used
- temporal-failing candidates are replay-gated
- row15 or row16 is omitted from first-replay status

## Evidence Gates

- M1038 must run no PPO
- M1038 must not promote
- M1038 must not use private holdout
- M1038 must preserve P0 actor inputs
- M1038 must gate M997 temporal retention before first replay
- M1038 must check M267/M264 row15 and M183/M170 row16 before any full gate claim

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote
- do not change actor inputs
- do not relax M997 thresholds
- do not drop M267/M264 row15
- do not drop M183/M170 row16
- do not run private holdout
- do not claim full public-gate or paper-level evidence

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1038-v4-public-base-candidate-b-combined-active-set-repair-projection-probe
- type: driver_candidate
- checkpoint: runs/m1038_candidate_b_combined_active_set_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a0_15.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: candidate_b_combined_active_set_projection_first_replay_candidate_route_to_full_public_gate_design
- reason: M1038 selects base_row16x4 alpha0.15 as a first-replay candidate passing M997 M297/M270 M267/M264 row15 and M183/M170 row16 with no PPO promotion or private holdout

## Next Blocker

m1039-v4-public-base-candidate-b-combined-active-set-full-public-gate-design
