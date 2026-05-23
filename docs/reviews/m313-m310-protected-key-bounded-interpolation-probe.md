# m313-m310-protected-key-bounded-interpolation-probe Research Review

## Summary

- Generated at UTC: 20260523T052311Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: admit_m314_full_public_gate_for_m313_a140
- Decision reason: M313 selects alpha 0.14 as largest protected-key-passing interpolation and it passes exact plus M183/M170 and M267/M264 first replay gates

## Hypothesis

A smaller interpolation from M307 toward the M310 repaired candidate can retain useful exact-objective movement while staying inside the protected-key normal-margin window.

## Lineage

- parent_checkpoint: runs/m306_exact_repair_from_raw_s40_seed10091/candidate_checkpoint.pt, runs/m310_exact_repair_from_raw_s40_seed10095/candidate_checkpoint.pt
- parent_dataset: runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz, runs/m133_zero_relvel_s60_strict_60ep_seed9900/outcome_sensitive_snippets.csv, runs/m133_zero_relvel_s60_strict_60ep_seed9920/outcome_sensitive_snippets.csv, runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv, runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv
- parent_config: experiments/manifests/m312-m310-protected-key-window-failure-audit.json, docs/m312-m310-protected-key-window-failure-audit.md
- parent_objective: salvage the M310 exact-repaired PPO direction with a protected-key-bounded trust-region interpolation
- derived_from: m312-m310-protected-key-window-failure-audit
- blocked_by: m312-m310-protected-key-window-failure-audit
- supersedes: None
- invalidates: None

## Success Criteria

- find an alpha greater than 0 that keeps exact M297 and M270 non-regressing versus M307
- selected alpha passes protected key 9944
- selected alpha passes M183/M170 and M267/M264 first replay gates
- if selected alpha is meaningful, admit a separate full public-gate milestone

## Failure Criteria

- no nonzero alpha passes protected key
- only negligible alpha passes
- selected alpha regresses exact M297 or M270
- selected alpha loses first replay retention
- actor input contract is changed

## Evidence Gates

- preserve human-view actor input contract
- generate M307-to-M310 interpolation checkpoints
- exact M297 and M270 no-regression versus M307
- protected key 9944 must pass and remain discriminative
- selected alpha must pass M183/M170 first replay gate
- selected alpha must pass M267/M264 first replay gate
- do not promote before a separate full public gate

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not bypass the protected-key window
- do not promote based on exact objectives alone
- do not run PPO
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m313-m310-protected-key-bounded-interpolation-probe
- type: driver_candidate
- checkpoint: runs/m313_m307_to_m310_protected_key_bounded_interpolation/checkpoints/alpha_0_14.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m314_full_public_gate_for_m313_a140
- reason: M313 selects alpha 0.14 as largest protected-key-passing interpolation and it passes exact plus M183/M170 and M267/M264 first replay gates

## Next Blocker

m314-full-public-gate-for-m313-a140
