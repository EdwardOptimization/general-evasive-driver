# m314-full-public-gate-for-m313-a140 Research Review

## Summary

- Generated at UTC: 20260523T052821Z
- Type: driver_candidate
- Gate tier: promotion
- Promotion decision: promote_m313_a140_public_gate_base
- Decision reason: M314 promotes alpha 0.14 after exact objectives six replay gates protected-key guard and behavior seeds all pass versus M307

## Hypothesis

The M313 alpha 0.14 protected-key-bounded interpolation candidate can pass the full public gate stack and become the next public-gate base.

## Lineage

- parent_checkpoint: runs/m306_exact_repair_from_raw_s40_seed10091/candidate_checkpoint.pt, runs/m313_m307_to_m310_protected_key_bounded_interpolation/checkpoints/alpha_0_14.pt
- parent_dataset: runs/m183_m168_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv, runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv, runs/m193_m189_boundary_outcome_corpus_seed9630/boundary_outcome_corpus.csv, runs/m212_m204_boundary_outcome_corpus_seed10040/boundary_outcome_corpus.csv, runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.csv, runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv, runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz, runs/m133_zero_relvel_s60_strict_60ep_seed9900/outcome_sensitive_snippets.csv, runs/m133_zero_relvel_s60_strict_60ep_seed9920/outcome_sensitive_snippets.csv
- parent_config: experiments/manifests/m313-m310-protected-key-bounded-interpolation-probe.json, docs/m313-m310-protected-key-bounded-interpolation-probe.md
- parent_objective: run full public promotion gate for M313 protected-key-bounded alpha 0.14
- derived_from: m313-m310-protected-key-bounded-interpolation-probe
- blocked_by: m313-m310-protected-key-bounded-interpolation-probe
- supersedes: None
- invalidates: None

## Success Criteria

- candidate passes all six public replay gates versus M307
- candidate passes protected-key diagnostic
- candidate retains behavior on seeds 9505 and 9506
- candidate keeps exact M297 and exact M270 improvements versus M307
- actor input contract remains unchanged

## Failure Criteria

- any replay gate fails
- protected key fails
- behavior seeds materially regress
- exact M297 or exact M270 regresses
- actor observation inputs change

## Evidence Gates

- candidate exact M297 and exact M270 remain non-regressing versus M307
- M183/M168 replay gate versus M307
- M183/M170 replay gate versus M307
- M193/M189 replay gate versus M307
- M212/M204 replay gate versus M307
- M223/M219 replay gate versus M307
- M267/M264 replay gate versus M307
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

- milestone: m314-full-public-gate-for-m313-a140
- type: driver_candidate
- checkpoint: runs/m313_m307_to_m310_protected_key_bounded_interpolation/checkpoints/alpha_0_14.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.8445855
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: promote_m313_a140_public_gate_base
- reason: M314 promotes alpha 0.14 after exact objectives six replay gates protected-key guard and behavior seeds all pass versus M307

## Next Blocker

m315-protected-key-aware-ppo-proposal-repeat-design
