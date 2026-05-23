# m336-full-public-gate-for-m335-a0075 Research Review

## Summary

- Generated at UTC: 20260523T072332Z
- Type: driver_candidate
- Gate tier: promotion
- Promotion decision: promote_m335_a0075_short_ppo_public_gate_base
- Decision reason: M336 promotes alpha 0.0075 after exact source-diverse six replay old-key gap floor and behavior gates pass but movement is micro-alpha bounded by old-key floor

## Hypothesis

The M335 alpha 0.0075 bounded short-PPO candidate may be promotable if it retains exact objectives, source-diverse protected proof, old-key gap floor, all six replay surfaces, and behavior seeds versus M333.

## Lineage

- parent_checkpoint: runs/m332_m328_to_m330_gap_bounded_interpolation/checkpoints/alpha_0_45.pt, runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_0075.pt
- parent_dataset: runs/m335_m333_to_repaired_exact_line_search/line_search_summary.csv, runs/m335_old_key_gap_sweep/guard_results.csv, runs/m335_a0075_source_diverse_protected_gate/summary.json, runs/m335_a0075_m183_m170_first_replay/summary.json, runs/m335_a0075_m267_m264_first_replay/summary.json, runs/m183_m168_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv, runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv, runs/m193_m189_boundary_outcome_corpus_seed9630/boundary_outcome_corpus.csv, runs/m212_m204_boundary_outcome_corpus_seed10040/boundary_outcome_corpus.csv, runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.csv, runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv
- parent_config: experiments/manifests/m335-short-source-diverse-ppo-escalation-run.json, docs/m335-short-source-diverse-ppo-escalation-run.md
- parent_objective: run full public promotion gate for M335 alpha 0.0075 bounded short-PPO candidate
- derived_from: m335-short-source-diverse-ppo-escalation-run
- blocked_by: m335-short-source-diverse-ppo-escalation-run
- supersedes: None
- invalidates: None

## Success Criteria

- candidate passes all six public replay gates versus M333
- candidate retains exact M297 and exact M270 improvements versus M333
- candidate keeps source-diverse protected proof
- candidate keeps old-key margin_gap >= 0.09
- candidate retains behavior on seeds 9505 and 9506
- actor input contract remains unchanged

## Failure Criteria

- any replay gate fails
- exact M297 or exact M270 regresses
- source-diverse protected proof fails
- old-key margin gap falls below 0.09
- behavior seeds materially regress
- actor observation inputs change

## Evidence Gates

- exact M297 and exact M270 remain non-regressing versus M333
- source-diverse protected gate remains passed
- old 9944 margin gap remains at least 0.09
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
- do not lower the old-key gap floor
- do not ignore source-diverse protected gate
- do not change actor inputs
- do not tune from private holdouts

## Failure Taxonomy

- none

## Scoreboard

- milestone: m336-full-public-gate-for-m335-a0075
- type: driver_candidate
- checkpoint: runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_0075.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.844540
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: promote_m335_a0075_short_ppo_public_gate_base
- reason: M336 promotes alpha 0.0075 after exact source-diverse six replay old-key gap floor and behavior gates pass but movement is micro-alpha bounded by old-key floor

## Next Blocker

m337-old-key-gap-floor-bottleneck-audit
