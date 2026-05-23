# m307-full-public-gate-for-m306-raw-s40 Research Review

## Summary

- Generated at UTC: 20260523T045632Z
- Type: driver_candidate
- Gate tier: promotion
- Promotion decision: promote_m306_raw_s40_public_gate_base
- Decision reason: M307 promotes m306_raw_s40 after exact objectives full replay protected-key and behavior gates all pass versus M299

## Hypothesis

The M306 raw-start exact repair candidate can pass the full public gate stack and become the next public-gate base.

## Lineage

- parent_checkpoint: runs/m298_rejected_preference_objective_only_probe/interpolation/checkpoints/alpha_0_02.pt, runs/m306_exact_repair_from_raw_s40_seed10091/candidate_checkpoint.pt
- parent_dataset: runs/m183_m168_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv, runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv, runs/m193_m189_boundary_outcome_corpus_seed9630/boundary_outcome_corpus.csv, runs/m212_m204_boundary_outcome_corpus_seed10040/boundary_outcome_corpus.csv, runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.csv, runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv, runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz
- parent_config: experiments/manifests/m306-repair-m302-raw-exact-projection-probe.json, docs/m306-repair-m302-raw-exact-projection-probe.md
- parent_objective: run full public replay protected-key and behavior gates for M306 raw-start exact repair candidate
- derived_from: m306-repair-m302-raw-exact-projection-probe
- blocked_by: m306-repair-m302-raw-exact-projection-probe
- supersedes: None
- invalidates: None

## Success Criteria

- candidate passes all six public replay gates versus M299
- candidate passes protected-key diagnostic
- candidate retains behavior on seeds 9505 and 9506
- candidate keeps exact M297 and exact M270 improvements versus M299
- actor input contract remains unchanged

## Failure Criteria

- any replay gate fails
- protected key fails
- behavior seeds materially regress
- exact M297 or exact M270 regresses
- actor observation inputs change

## Evidence Gates

- candidate exact M297 and exact M270 remain non-regressing versus M299
- M183/M168 replay gate
- M183/M170 replay gate
- M193/M189 replay gate
- M212/M204 replay gate
- M223/M219 replay gate
- M267/M264 replay gate
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

- milestone: m307-full-public-gate-for-m306-raw-s40
- type: driver_candidate
- checkpoint: runs/m306_exact_repair_from_raw_s40_seed10091/candidate_checkpoint.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.844585
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: promote_m306_raw_s40_public_gate_base
- reason: M307 promotes m306_raw_s40 after exact objectives full replay protected-key and behavior gates all pass versus M299

## Next Blocker

m308-exact-repair-fresh-seed-repeat
