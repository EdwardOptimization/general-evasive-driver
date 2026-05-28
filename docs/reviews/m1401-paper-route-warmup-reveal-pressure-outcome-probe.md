# m1401-paper-route-warmup-reveal-pressure-outcome-probe Research Review

## Summary

- Generated at UTC: 20260528T235702Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: late_reveal_margin_banded_outcome_action_only_route_to_result_audit
- Decision reason: M1401 finds 1464 action-critical rows but 0 accepted outcome rows and 0 preferred near-boundary candidates so late reveal alone is insufficient

## Hypothesis

No-training margin-banded outcome interventions over M1400 late-reveal rows can determine whether stronger reveal pressure creates source-diverse history-relevant outcome gaps.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: docs/m1400-paper-route-warmup-reveal-pressure-source-smoke.md, runs/m1400_warmup_reveal_pressure_source_smoke/summary.json, runs/m1400_warmup_reveal_pressure_source_smoke/matched_or_bucketed_rows.csv
- parent_config: experiments/manifests/m1400-paper-route-warmup-reveal-pressure-source-smoke.json
- parent_objective: run or implement margin-banded no-training outcome probe over late-reveal matched/bucketed rows
- derived_from: m1400-paper-route-warmup-reveal-pressure-source-smoke
- blocked_by: M1400 materialized late-reveal source rows but did not test normal margin bands or outcome interventions
- supersedes: training directly from M1400 source rows, claiming self-identification from late-reveal source materialization
- invalidates: None

## Success Criteria

- runs/m1401_warmup_reveal_pressure_outcome_probe/summary.json exists
- normal reset zero-current delayed wrong-warmup same-recent-wrong-warmup and shortened/removed-warmup variants are reported or cleanly rejected
- normal-margin bands and accepted-row source/reveal-step diversity are reported
- result chooses next route without training, PPO, promotion, private holdout, training corpus export, or actor-input expansion

## Failure Criteria

- outcome probe artifact is missing
- normal-margin band reporting is missing
- source or reveal-step diversity is not reported
- result routes directly to training or claim expansion

## Evidence Gates

- M1401 must run or implement no-training outcome interventions over M1400 matched/bucketed rows
- M1401 must report normal-margin bands and strict-vs-bucketed accepted-row splits
- M1401 must report reveal-step and source-diversity splits for accepted rows
- M1401 must not train, run PPO, promote, use private holdout, export a training corpus, or change actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export corpus
- do not count reset-only or zero-current-only rows as self-identification
- do not count source materialization as outcome evidence
- do not claim level3 self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1401-paper-route-warmup-reveal-pressure-outcome-probe
- type: infrastructure
- checkpoint: runs/m1401_warmup_reveal_pressure_outcome_probe/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: late_reveal_margin_banded_outcome_action_only_route_to_result_audit
- reason: M1401 finds 1464 action-critical rows but 0 accepted outcome rows and 0 preferred near-boundary candidates so late reveal alone is insufficient

## Next Blocker

m1402-paper-route-warmup-reveal-pressure-outcome-result-audit
