# m1400-paper-route-warmup-reveal-pressure-source-smoke Research Review

## Summary

- Generated at UTC: 20260528T235220Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: late_reveal_source_smoke_structural_pass_admit_margin_banded_outcome_probe
- Decision reason: M1400 materializes 1604 late-reveal source rows and 256 matched/bucketed rows at steps 64 72 80 without outcome probing or training

## Hypothesis

A no-training late-reveal source smoke can materialize matched or bucketed warmup-latched rows while increasing reveal pressure relative to M1394.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: docs/m1399-paper-route-warmup-reveal-pressure-redesign.md, runs/m1397_warmup_latched_outcome_full_sweep/summary.json
- parent_config: experiments/manifests/m1399-paper-route-warmup-reveal-pressure-redesign.json, configs/m991_capability_step_fault_source_wave.json
- parent_objective: run no-training late-reveal warmup/reveal pressure source smoke
- derived_from: m1399-paper-route-warmup-reveal-pressure-redesign
- blocked_by: M1399 requires structural late-reveal viability before outcome probing
- supersedes: running another M1394 reveal grid, running outcome interventions before late-reveal source viability is known
- invalidates: None

## Success Criteria

- runs/m1400_warmup_reveal_pressure_source_smoke/summary.json exists
- warmup and reveal structure is reported
- matching and source-diversity metrics are reported
- result compares structural viability against M1394
- result chooses next route without outcome intervention, training, PPO, promotion, private holdout, corpus export, or actor-input expansion

## Failure Criteria

- source smoke artifact is missing
- warmup/reveal structure is not measured
- matching or source-diversity metrics are not reported
- result routes directly to outcome interpretation, training, or claim expansion

## Evidence Gates

- M1400 must run a no-training late-reveal source smoke using the existing warmup_latched_config_smoke runner
- M1400 must report warmup/reveal structure, matching metrics, and source diversity
- M1400 must compare structural viability against M1394
- M1400 must not run outcome interventions, train, run PPO, promote, use private holdout, export a training corpus, or change actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run outcome interventions
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export corpus
- do not relax matching thresholds after seeing M1397
- do not claim self-identification from source materialization

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1400-paper-route-warmup-reveal-pressure-source-smoke
- type: infrastructure
- checkpoint: runs/m1400_warmup_reveal_pressure_source_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: late_reveal_source_smoke_structural_pass_admit_margin_banded_outcome_probe
- reason: M1400 materializes 1604 late-reveal source rows and 256 matched/bucketed rows at steps 64 72 80 without outcome probing or training

## Next Blocker

m1401-paper-route-warmup-reveal-pressure-outcome-probe
