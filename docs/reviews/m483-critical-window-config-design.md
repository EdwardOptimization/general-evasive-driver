# m483-critical-window-config-design Research Review

## Summary

- Generated at UTC: 20260523T223455Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: admit_m484_critical_window_config_implementation
- Decision reason: M483 designs near-threshold and late high-energy critical-window zero-relvel configs plus sampling stress before any proof mining or training

## Hypothesis

Because M482 tail-aligned wrong-history swaps create event rows only on a single source pair, a stricter critical-window task family is needed to reduce recovery time and expose source-diverse natural wrong-history event proof.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m482_tail_aligned_wrong_history_gate/summary.json, runs/m482_tail_aligned_wrong_history_gate/tail_outcomes.csv, runs/m474_combined_fresh_anchor_adversarial_search/adversarial_pairs.csv
- parent_config: configs/m457_history_necessity_late_reveal_zero_relvel.json, experiments/manifests/m482-tail-aligned-wrong-history-gate-implementation.json
- parent_objective: critical-window config design after source-narrow tail-aligned event signal
- derived_from: m482-tail-aligned-wrong-history-gate-implementation
- blocked_by: m482-tail-aligned-wrong-history-gate-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- document why M482 remains diagnostic-only
- define one or more critical-window config variants with concrete parameter changes
- define reset/sampling stress tests before any proof run
- define the next implementation manifest
- preserve the P0 actor-input contract
- no checkpoint is promoted

## Failure Criteria

- design treats single-pair M482 events as proof
- design proposes training before config sampling validity is checked
- design changes actor inputs
- design loosens source-diversity gates

## Evidence Gates

- treat M482 tail-aligned event rows as diagnostic because they are source-narrow
- design critical-window config variants that reduce recovery time after obstacle reveal
- preserve zero obstacle relative velocity and P0 human-view actor inputs
- define sampling stress tests before any tail-aligned proof mining
- no checkpoint promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not count single-pair repeated tail events as source-diverse proof
- do not relax event/source-diversity thresholds
- do not tune from private holdouts

## Failure Taxonomy

- none

## Scoreboard

- milestone: m483-critical-window-config-design
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m484_critical_window_config_implementation
- reason: M483 designs near-threshold and late high-energy critical-window zero-relvel configs plus sampling stress before any proof mining or training

## Next Blocker

m484-critical-window-config-implementation
