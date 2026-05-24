# m703-extreme-dynamics-scenario-corpus-design Research Review

## Summary

- Generated at UTC: 20260524T181428Z
- Type: infrastructure
- Gate tier: generalization
- Promotion decision: extreme_dynamics_scenario_corpus_design_admit_m704
- Decision reason: M703 designs current-model hidden capability faults future four-wheel-only fault boundaries warm-up timing matched hidden-condition corpus gates and no-training M704 implementation artifacts

## Hypothesis

A designed extreme hidden-condition scenario corpus can create matched current-state cases where online command-response history is necessary for evasive driving decisions.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m702-boundary-sensitivity-scale-diagnostic-audit.md, runs/m701_boundary_sensitivity_scale_diagnostic/summary.json, runs/m701_boundary_sensitivity_scale_diagnostic/scale_summary.csv, runs/m701_boundary_sensitivity_scale_diagnostic/window_summary.csv
- parent_config: experiments/manifests/m702-boundary-sensitivity-scale-diagnostic-audit.json
- parent_objective: design extreme hidden-condition scenario corpus after source-mining branch pivot
- derived_from: m702-boundary-sensitivity-scale-diagnostic-audit
- blocked_by: m702-boundary-sensitivity-scale-diagnostic-audit
- supersedes: None
- invalidates: None

## Success Criteria

- design defines current-model-compatible fault families
- design defines future four-wheel-only fault families separately
- design defines severity ladders and warm-up timing
- design defines matched hidden-condition pair criteria
- design defines no-training artifacts
- design defines source-positive and negative-result classifications
- objective actor update PPO and promotion remain blocked

## Failure Criteria

- design adds hidden fault labels to actor input
- design treats true single-wheel failures as available in the current single-track model
- design omits matched hidden-condition ambiguity
- design admits actor update or PPO before source-positive evidence
- design changes actor input contract

## Evidence Gates

- design covers current-model hidden capability faults
- design distinguishes current single-track proxies from future true four-wheel faults
- design keeps hidden fault labels out of actor input
- design specifies matched hidden-condition ambiguity requirements
- design blocks actor update PPO and promotion
- design defines no-training corpus artifacts and acceptance criteria

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor
- do not run PPO
- do not promote a checkpoint
- do not add fault labels to actor observations
- do not call single-track proxies true single-wheel failures
- do not generate only hard scenarios without matched hidden-condition ambiguity
- do not reintroduce reference-path or TTC oracle inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m703-extreme-dynamics-scenario-corpus-design
- type: infrastructure
- checkpoint: docs/m703-extreme-dynamics-scenario-corpus-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: extreme_dynamics_scenario_corpus_design_admit_m704
- reason: M703 designs current-model hidden capability faults future four-wheel-only fault boundaries warm-up timing matched hidden-condition corpus gates and no-training M704 implementation artifacts

## Next Blocker

m704-extreme-dynamics-scenario-corpus-implementation
