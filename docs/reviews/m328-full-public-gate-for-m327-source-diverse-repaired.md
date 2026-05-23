# m328-full-public-gate-for-m327-source-diverse-repaired Research Review

## Summary

- Generated at UTC: 20260523T064312Z
- Type: driver_candidate
- Gate tier: promotion
- Promotion decision: promote_m327_source_diverse_repaired_public_gate_base
- Decision reason: M328 promotes M327 repaired after exact objectives improve plus 3/3 source-diverse gates pass plus 6/6 replay gates pass plus 9944 singleton-window gap 0.092653 plus behavior seeds retain

## Hypothesis

The M327 exact-repaired PPO proposal may be promotable if it retains exact objectives, source-diverse protected proof, all six replay surfaces, old-key singleton-window audit, and behavior seeds versus M325.

## Lineage

- parent_checkpoint: runs/m316_exact_repair_from_raw_s40_seed10096/candidate_checkpoint.pt, runs/m327_exact_repair_from_raw_s40_seed10097/candidate_checkpoint.pt
- parent_dataset: runs/m327_source_diverse_protected_gate/summary.json, runs/m327_critical_key_seed9944/guard_results.csv, runs/m327_m183_m170_first_replay/summary.json, runs/m327_m267_m264_first_replay/summary.json, runs/m183_m168_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv, runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv, runs/m193_m189_boundary_outcome_corpus_seed9630/boundary_outcome_corpus.csv, runs/m212_m204_boundary_outcome_corpus_seed10040/boundary_outcome_corpus.csv, runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.csv, runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv
- parent_config: experiments/manifests/m327-source-diverse-protected-ppo-proposal-smoke.json, docs/m327-source-diverse-protected-ppo-proposal-smoke.md
- parent_objective: run full public promotion gate for M327 exact-repaired PPO proposal
- derived_from: m327-source-diverse-protected-ppo-proposal-smoke
- blocked_by: m327-source-diverse-protected-ppo-proposal-smoke
- supersedes: None
- invalidates: None

## Success Criteria

- candidate passes all six public replay gates versus M325
- candidate retains exact M297 and exact M270 improvements versus M325
- candidate keeps source-diverse protected proof
- old 9944 diagnostic is reported and classified
- candidate retains behavior on seeds 9505 and 9506
- actor input contract remains unchanged

## Failure Criteria

- any replay gate fails
- exact M297 or exact M270 regresses
- source-diverse protected proof fails
- old-key failure is not singleton-window-only
- behavior seeds materially regress
- actor observation inputs change

## Evidence Gates

- exact M297 and exact M270 remain non-regressing versus M325
- source-diverse protected gate remains passed
- old 9944 diagnostic is classified explicitly
- M183/M168 replay gate versus M325
- M183/M170 replay gate versus M325
- M193/M189 replay gate versus M325
- M212/M204 replay gate versus M325
- M223/M219 replay gate versus M325
- M267/M264 replay gate versus M325
- behavior seeds 9505 and 9506
- research validator

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not promote on first replay gates alone
- do not ignore source-diverse protected gate
- do not hide 9944 diagnostic
- do not change actor inputs
- do not tune from private holdouts

## Failure Taxonomy

- none

## Scoreboard

- milestone: m328-full-public-gate-for-m327-source-diverse-repaired
- type: driver_candidate
- checkpoint: runs/m327_exact_repair_from_raw_s40_seed10097/candidate_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: promote_m327_source_diverse_repaired_public_gate_base
- reason: M328 promotes M327 repaired after exact objectives improve plus 3/3 source-diverse gates pass plus 6/6 replay gates pass plus 9944 singleton-window gap 0.092653 plus behavior seeds retain

## Next Blocker

m329-source-diverse-ppo-fresh-seed-repeat-design
