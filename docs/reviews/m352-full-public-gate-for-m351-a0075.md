# m352-full-public-gate-for-m351-a0075 Research Review

## Summary

- Generated at UTC: 20260523T103651Z
- Type: driver_candidate
- Gate tier: promotion
- Promotion decision: promote_m351_a0075_old_key_neighborhood_public_gate_base
- Decision reason: M352 promotes alpha 0.0075 after exact source-diverse old-key neighborhood six replay and behavior gates pass

## Hypothesis

The M351 alpha 0.0075 bounded PPO candidate may be promotable if it retains exact objectives, source-diverse protected proof, old-key neighborhood proof, all six replay surfaces, and behavior seeds.

## Lineage

- parent_checkpoint: runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_01.pt, runs/m351_m349_to_repaired_old_key_neighborhood_interpolation/checkpoints/alpha_0_0075.pt
- parent_dataset: runs/m351_old_key_neighborhood_ppo_escalation/summary.json, runs/m351_a0075_exact_eval_vs_m349/summary.json, runs/m351_a0075_source_diverse_protected_gate/summary.json, runs/m351_old_key_neighborhood_alpha_sweep/gates_with_diagnostic/m351_a0075/summary.json, runs/m351_a0075_m183_m170_first_replay/summary.json, runs/m351_a0075_m267_m264_first_replay/summary.json, runs/m183_m168_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv, runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv, runs/m193_m189_boundary_outcome_corpus_seed9630/boundary_outcome_corpus.csv, runs/m212_m204_boundary_outcome_corpus_seed10040/boundary_outcome_corpus.csv, runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.csv, runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv
- parent_config: experiments/manifests/m351-old-key-neighborhood-ppo-escalation-run.json, docs/m351-old-key-neighborhood-ppo-escalation-run.md
- parent_objective: run full public promotion gate for M351 alpha 0.0075 bounded short-PPO candidate
- derived_from: m351-old-key-neighborhood-ppo-escalation-run
- blocked_by: m351-old-key-neighborhood-ppo-escalation-run
- supersedes: None
- invalidates: None

## Success Criteria

- candidate passes all six public replay gates versus M333
- candidate retains exact M297 and exact M270 no-regression versus M349
- candidate keeps source-diverse protected proof
- candidate keeps old-key neighborhood proof
- candidate retains behavior on seeds 9505 and 9506
- actor input contract remains unchanged

## Failure Criteria

- any replay gate fails
- exact M297 or exact M270 regresses versus M349
- source-diverse protected proof fails
- old-key neighborhood proof fails
- behavior seeds materially regress
- actor observation inputs change

## Evidence Gates

- exact M297 and exact M270 remain non-regressing versus M349
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
- do not skip the old-key neighborhood gate
- do not restore singleton 9944 as the only old-key gate
- do not ignore source-diverse protected gate
- do not change actor inputs
- do not tune from private holdouts

## Failure Taxonomy

- none

## Scoreboard

- milestone: m352-full-public-gate-for-m351-a0075
- type: driver_candidate
- checkpoint: runs/m351_m349_to_repaired_old_key_neighborhood_interpolation/checkpoints/alpha_0_0075.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.844538
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: promote_m351_a0075_old_key_neighborhood_public_gate_base
- reason: M352 promotes alpha 0.0075 after exact source-diverse old-key neighborhood six replay and behavior gates pass

## Next Blocker

m353-old-key-neighborhood-ppo-fresh-seed-repeat-design
