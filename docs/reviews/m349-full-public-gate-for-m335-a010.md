# m349-full-public-gate-for-m335-a010 Research Review

## Summary

- Generated at UTC: 20260523T102042Z
- Type: driver_candidate
- Gate tier: promotion
- Promotion decision: promote_m335_a010_old_key_neighborhood_public_gate_base
- Decision reason: M349 promotes alpha 0.01 after exact source-diverse old-key neighborhood six replay and behavior gates pass

## Hypothesis

The M335 alpha 0.01 candidate may be promotable if it retains exact objectives, source-diverse protected proof, old-key neighborhood proof, all six replay surfaces, and behavior seeds.

## Lineage

- parent_checkpoint: runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_0075.pt, runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_01.pt
- parent_dataset: runs/m348_m335_a010_probe/summary.json, runs/m348_m335_a010_exact_eval_vs_a0075/summary.json, runs/m348_m335_a010_source_diverse_protected_gate/summary.json, runs/m348_m335_a010_m183_m170_first_replay/summary.json, runs/m348_m335_a010_m267_m264_first_replay/summary.json, runs/m347_old_key_alpha_sweep/summary.json, runs/m183_m168_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv, runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv, runs/m193_m189_boundary_outcome_corpus_seed9630/boundary_outcome_corpus.csv, runs/m212_m204_boundary_outcome_corpus_seed10040/boundary_outcome_corpus.csv, runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.csv, runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv
- parent_config: experiments/manifests/m348-exact-source-diverse-probe-for-m335-a010.json, docs/m348-exact-source-diverse-probe-for-m335-a010.md
- parent_objective: run full public promotion gate for M335 alpha 0.01 after M348 proof-gate pass
- derived_from: m348-exact-source-diverse-probe-for-m335-a010
- blocked_by: m348-exact-source-diverse-probe-for-m335-a010
- supersedes: None
- invalidates: None

## Success Criteria

- candidate passes all six public replay gates versus M333
- candidate retains exact M297 and exact M270 no-regression versus current M336 base
- candidate keeps source-diverse protected proof
- candidate keeps old-key neighborhood proof from M347/M348
- candidate retains behavior on seeds 9505 and 9506
- actor input contract remains unchanged

## Failure Criteria

- any replay gate fails
- exact M297 or exact M270 regresses versus current M336 base
- source-diverse protected proof fails
- old-key neighborhood proof fails
- behavior seeds materially regress
- actor observation inputs change

## Evidence Gates

- exact M297 and exact M270 remain non-regressing versus current M336 base
- source-diverse protected gate remains passed
- old-key neighborhood replay gate remains passed
- M183/M168 replay gate versus M333
- M183/M170 replay gate versus M333
- M193/M189 replay gate versus M333
- M212/M204 replay gate versus M333
- M223/M219 replay gate versus M333
- M267/M264 replay gate versus M333
- behavior seeds 9505 and 9506
- research validator

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not promote on first replay gates alone
- do not restore singleton 9944 as a standalone veto when the old-key neighborhood gate passes
- do not skip the old-key neighborhood gate
- do not ignore source-diverse protected gate
- do not change actor inputs
- do not tune from private holdouts

## Failure Taxonomy

- none

## Scoreboard

- milestone: m349-full-public-gate-for-m335-a010
- type: driver_candidate
- checkpoint: runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_01.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.844540
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: promote_m335_a010_old_key_neighborhood_public_gate_base
- reason: M349 promotes alpha 0.01 after exact source-diverse old-key neighborhood six replay and behavior gates pass

## Next Blocker

m350-old-key-neighborhood-ppo-escalation-design
