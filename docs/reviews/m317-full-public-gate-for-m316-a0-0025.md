# m317-full-public-gate-for-m316-a0-0025 Research Review

## Summary

- Generated at UTC: 20260523T054447Z
- Type: driver_candidate
- Gate tier: promotion
- Promotion decision: promote_m316_a0_0025_public_gate_base
- Decision reason: M317 promotes m316_a0_0025 after exact objectives six replay gates protected-key guard and behavior seeds all pass versus M314 but protected-key slack is only about 4.8e-6

## Hypothesis

The M316 alpha 0.0025 protected-key-bounded PPO proposal can pass the full public gate stack and become the next public-gate base despite its tiny step size.

## Lineage

- parent_checkpoint: runs/m313_m307_to_m310_protected_key_bounded_interpolation/checkpoints/alpha_0_14.pt, runs/m316_m314_to_repaired_protected_key_bounded_interpolation/checkpoints/alpha_0_0025.pt
- parent_dataset: runs/m183_m168_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv, runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv, runs/m193_m189_boundary_outcome_corpus_seed9630/boundary_outcome_corpus.csv, runs/m212_m204_boundary_outcome_corpus_seed10040/boundary_outcome_corpus.csv, runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.csv, runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv, runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz, runs/m133_zero_relvel_s60_strict_60ep_seed9900/outcome_sensitive_snippets.csv, runs/m133_zero_relvel_s60_strict_60ep_seed9920/outcome_sensitive_snippets.csv
- parent_config: experiments/manifests/m316-protected-key-aware-ppo-proposal-smoke.json, docs/m316-protected-key-aware-ppo-proposal-smoke.md
- parent_objective: run full public promotion gate for M316 protected-key-bounded alpha 0.0025
- derived_from: m316-protected-key-aware-ppo-proposal-smoke
- blocked_by: m316-protected-key-aware-ppo-proposal-smoke
- supersedes: None
- invalidates: None

## Success Criteria

- candidate passes all six public replay gates versus M314
- candidate passes protected-key diagnostic
- candidate retains behavior on seeds 9505 and 9506
- candidate keeps exact M297 and exact M270 no-regression versus M314
- actor input contract remains unchanged

## Failure Criteria

- any replay gate fails
- protected key fails
- behavior seeds materially regress
- exact M297 or exact M270 regresses
- actor observation inputs change

## Evidence Gates

- candidate exact M297 and exact M270 remain non-regressing versus M314
- M183/M168 replay gate versus M314
- M183/M170 replay gate versus M314
- M193/M189 replay gate versus M314
- M212/M204 replay gate versus M314
- M223/M219 replay gate versus M314
- M267/M264 replay gate versus M314
- protected key 9944 guard
- behavior seeds 9505 and 9506
- research validator

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not promote on first replay gates alone
- do not loosen protected-key or behavior gates
- do not change actor inputs
- do not ignore exact M297 or exact M270 regression

## Failure Taxonomy

- none

## Scoreboard

- milestone: m317-full-public-gate-for-m316-a0-0025
- type: driver_candidate
- checkpoint: runs/m316_m314_to_repaired_protected_key_bounded_interpolation/checkpoints/alpha_0_0025.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.8445853
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: promote_m316_a0_0025_public_gate_base
- reason: M317 promotes m316_a0_0025 after exact objectives six replay gates protected-key guard and behavior seeds all pass versus M314 but protected-key slack is only about 4.8e-6

## Next Blocker

m318-m317-protected-key-slack-audit
