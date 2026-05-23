# m316-protected-key-aware-ppo-proposal-smoke Research Review

## Summary

- Generated at UTC: 20260523T053945Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: admit_m317_full_public_gate_for_m316_a0_0025
- Decision reason: M316 raw PPO regresses exact M297/M270 but exact repair recovers both; protected key allows only alpha 0.0025 which passes M183/M170 and M267/M264 first replay gates

## Hypothesis

A fresh smoke-scale PPO proposal from the M314 base can produce useful movement if exact repair and protected-key-bounded interpolation are enforced before replay gates.

## Lineage

- parent_checkpoint: runs/m313_m307_to_m310_protected_key_bounded_interpolation/checkpoints/alpha_0_14.pt
- parent_dataset: runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz, runs/m133_zero_relvel_s60_strict_60ep_seed9900/outcome_sensitive_snippets.csv, runs/m133_zero_relvel_s60_strict_60ep_seed9920/outcome_sensitive_snippets.csv, runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv, runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv
- parent_config: configs/ppo_m316_protected_key_aware_proposal_smoke.json, experiments/manifests/m315-protected-key-aware-ppo-proposal-repeat-design.json, docs/m315-protected-key-aware-ppo-proposal-repeat-design.md
- parent_objective: run fresh smoke PPO proposal from M314 base and accept only through exact repair plus protected-key-bounded interpolation
- derived_from: m315-protected-key-aware-ppo-proposal-repeat-design
- blocked_by: m315-protected-key-aware-ppo-proposal-repeat-design
- supersedes: None
- invalidates: None

## Success Criteria

- raw PPO run completes from M314 base
- exact repair candidate improves or retains exact M297 and exact M270 versus M314
- a nonzero interpolation alpha passes exact objectives and protected key 9944
- selected alpha passes M183/M170 and M267/M264 first replay gates
- if first gates pass, admit a separate full public-gate milestone

## Failure Criteria

- raw PPO cannot run or checkpoint is incompatible
- repaired candidate regresses exact M297 or exact M270
- no nonzero protected-key-safe alpha exists
- selected alpha loses first replay retention
- actor input contract is changed

## Evidence Gates

- preserve human-view actor input contract
- run smoke PPO from M314 only as a raw proposal
- run exact post-PPO repair from raw proposal
- exact M297 and M270 must not regress versus M314
- protected key 9944 must pass for selected alpha
- M183/M170 first replay gate
- M267/M264 first replay gate
- do not run full public gate unless exact protected-key and first replay gates pass

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not promote raw PPO checkpoint
- do not run replay for exact-regressing candidates
- do not run replay for protected-key-failing candidates
- do not change actor inputs
- do not tune from private holdouts

## Failure Taxonomy

- none

## Scoreboard

- milestone: m316-protected-key-aware-ppo-proposal-smoke
- type: driver_candidate
- checkpoint: runs/m316_m314_to_repaired_protected_key_bounded_interpolation/checkpoints/alpha_0_0025.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m317_full_public_gate_for_m316_a0_0025
- reason: M316 raw PPO regresses exact M297/M270 but exact repair recovers both; protected key allows only alpha 0.0025 which passes M183/M170 and M267/M264 first replay gates

## Next Blocker

m317-full-public-gate-for-m316-a0-0025
