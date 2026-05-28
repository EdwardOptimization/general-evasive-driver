# m1391-paper-route-causal-history-source-miner-implementation Research Review

## Summary

- Generated at UTC: 20260528T230455Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: causal_history_source_miner_structural_pass_admit_candidate_outcome_probe
- Decision reason: M1391 materializes 631 matched-current source candidates across 46 seeds and 9 fault pairs; structural source pass but not history proof so outcome interventions are next

## Hypothesis

A no-training source miner can materialize matched-current older-history candidates and source-diversity diagnostics for the causal history-necessity branch.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: docs/m1390-paper-route-causal-history-necessity-task-design.md, runs/m1375_promoted_base_source_rich_public_wave/reset_only_rows.csv, runs/m1379_promoted_base_source_rich_sequence_expanded_probe/summary.json
- parent_config: experiments/manifests/m1390-paper-route-causal-history-necessity-task-design.json
- parent_objective: materialize no-training matched-current older-history source candidates before corpus export or training
- derived_from: m1390-paper-route-causal-history-necessity-task-design
- blocked_by: M1390 requires causal history-necessity source materialization before new profile scaling or training
- supersedes: running another blind history-profile repeat, exporting a temporal corpus from seed-thin M1379 rows
- invalidates: None

## Success Criteria

- source miner implementation or smoke artifact exists
- matching-distance histograms are reported
- source-diversity metrics are reported
- result chooses next route without training, PPO, promotion, private holdout, training corpus export, or actor-input expansion

## Failure Criteria

- source miner artifact is missing
- matching distances are not measured
- source diversity is not measured
- result routes directly to training or claim expansion

## Evidence Gates

- M1391 must implement or run a no-training public source miner/smoke
- M1391 must report matched-current distance histograms and source diversity
- M1391 must report whether structural smoke thresholds are met
- M1391 must not train, run PPO, promote, use private holdout, export a training corpus, or change actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export a training corpus
- do not claim level3 self-identification
- do not relax matching thresholds after seeing results

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1391-paper-route-causal-history-source-miner-implementation
- type: infrastructure
- checkpoint: runs/m1391_causal_history_source_miner/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: causal_history_source_miner_structural_pass_admit_candidate_outcome_probe
- reason: M1391 materializes 631 matched-current source candidates across 46 seeds and 9 fault pairs; structural source pass but not history proof so outcome interventions are next

## Next Blocker

m1392-paper-route-causal-history-candidate-outcome-probe
