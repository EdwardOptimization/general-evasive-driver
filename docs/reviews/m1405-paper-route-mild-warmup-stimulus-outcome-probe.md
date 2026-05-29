# m1405-paper-route-mild-warmup-stimulus-outcome-probe Research Review

## Summary

- Generated at UTC: 20260529T001506Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: mild_warmup_outcome_reset_only_route_to_result_audit
- Decision reason: M1405 improves preferred near-boundary candidates to 26 but finds 0 warmup-history-positive rows and only 2 high-margin reset-hidden accepted rows from 1 seed

## Hypothesis

No-training margin-banded outcome interventions over M1404 mild warmup stimulus rows can determine whether the figure-eight stimulus creates source-diverse history-relevant outcome gaps.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: docs/m1404-paper-route-mild-warmup-stimulus-source-smoke.md, runs/m1404_mild_warmup_stimulus_source_smoke/summary.json, runs/m1404_mild_warmup_stimulus_source_smoke/matched_or_bucketed_rows.csv
- parent_config: experiments/manifests/m1404-paper-route-mild-warmup-stimulus-source-smoke.json, configs/m1404_mild_warmup_stimulus_source_wave.json
- parent_objective: run no-training margin-banded outcome probe over M1404 mild warmup stimulus matched/bucketed rows
- derived_from: m1404-paper-route-mild-warmup-stimulus-source-smoke
- blocked_by: M1404 source smoke structurally passed but did not test outcome interventions
- supersedes: training directly from M1404 source rows, claiming self-identification from M1404 source materialization
- invalidates: None

## Success Criteria

- runs/m1405_mild_warmup_stimulus_outcome_probe/summary.json exists
- normal reset zero-current delayed wrong-warmup same-recent-wrong-warmup and shortened/removed-warmup variants are reported or cleanly rejected
- normal-margin bands and accepted-row source/reveal-step diversity are reported
- result chooses next route without training, PPO, promotion, private holdout, training corpus export, or actor-input expansion

## Failure Criteria

- outcome probe artifact is missing
- normal-margin band reporting is missing
- source or reveal-step diversity is not reported
- result routes directly to training or claim expansion

## Evidence Gates

- M1405 must run no-training outcome interventions over M1404 matched/bucketed rows
- M1405 must report normal-margin bands and accepted-row source/reveal-step diversity
- M1405 must separate wrong-warmup and delayed-history variants from reset/zero-current controls
- M1405 must not train, run PPO, promote, use private holdout, export a training corpus, or change actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export corpus
- do not count source materialization as outcome evidence
- do not count action-only evidence as self-identification
- do not claim level3 self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1405-paper-route-mild-warmup-stimulus-outcome-probe
- type: infrastructure
- checkpoint: runs/m1405_mild_warmup_stimulus_outcome_probe/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: mild_warmup_outcome_reset_only_route_to_result_audit
- reason: M1405 improves preferred near-boundary candidates to 26 but finds 0 warmup-history-positive rows and only 2 high-margin reset-hidden accepted rows from 1 seed

## Next Blocker

m1406-paper-route-mild-warmup-outcome-result-audit
