# m333-full-public-gate-for-m332-a045 Research Review

## Summary

- Generated at UTC: 20260523T070806Z
- Type: driver_candidate
- Gate tier: promotion
- Promotion decision: promote_m332_a045_source_diverse_public_gate_base
- Decision reason: M333 promotes alpha 0.45 after exact objectives improve plus 4/4 source-diverse gates pass plus 6/6 replay gates pass plus 9944 gap floor 0.090155 plus behavior seeds retain

## Hypothesis

The M332 alpha 0.45 interpolation candidate may be promotable if it retains exact objectives, source-diverse protected proof, old-key gap floor, all six replay surfaces, and behavior seeds versus M328.

## Lineage

- parent_checkpoint: runs/m327_exact_repair_from_raw_s40_seed10097/candidate_checkpoint.pt, runs/m332_m328_to_m330_gap_bounded_interpolation/checkpoints/alpha_0_45.pt
- parent_dataset: runs/m332_m328_to_m330_exact_line_search/line_search_summary.csv, runs/m332_old_key_gap_sweep/guard_results.csv, runs/m332_a045_source_diverse_protected_gate/summary.json, runs/m332_a045_m183_m170_first_replay/summary.json, runs/m332_a045_m267_m264_first_replay/summary.json, runs/m183_m168_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv, runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv, runs/m193_m189_boundary_outcome_corpus_seed9630/boundary_outcome_corpus.csv, runs/m212_m204_boundary_outcome_corpus_seed10040/boundary_outcome_corpus.csv, runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.csv, runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv
- parent_config: experiments/manifests/m332-m330-old-key-gap-bounded-interpolation-probe.json, docs/m332-m330-old-key-gap-bounded-interpolation-probe.md
- parent_objective: run full public promotion gate for M332 alpha 0.45 gap-bounded interpolation candidate
- derived_from: m332-m330-old-key-gap-bounded-interpolation-probe
- blocked_by: m332-m330-old-key-gap-bounded-interpolation-probe
- supersedes: None
- invalidates: None

## Success Criteria

- candidate passes all six public replay gates versus M328
- candidate retains exact M297 and exact M270 improvements versus M328
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

- exact M297 and exact M270 remain non-regressing versus M328
- source-diverse protected gate remains passed
- old 9944 margin gap remains at least 0.09
- M183/M168 replay gate versus M328
- M183/M170 replay gate versus M328
- M193/M189 replay gate versus M328
- M212/M204 replay gate versus M328
- M223/M219 replay gate versus M328
- M267/M264 replay gate versus M328
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

- milestone: m333-full-public-gate-for-m332-a045
- type: driver_candidate
- checkpoint: runs/m332_m328_to_m330_gap_bounded_interpolation/checkpoints/alpha_0_45.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.844541
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: promote_m332_a045_source_diverse_public_gate_base
- reason: M333 promotes alpha 0.45 after exact objectives improve plus 4/4 source-diverse gates pass plus 6/6 replay gates pass plus 9944 gap floor 0.090155 plus behavior seeds retain

## Next Blocker

m334-short-source-diverse-ppo-escalation-design
