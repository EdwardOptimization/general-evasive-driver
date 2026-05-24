# m704-extreme-dynamics-scenario-corpus-implementation Research Review

## Summary

- Generated at UTC: 20260524T182613Z
- Type: infrastructure
- Gate tier: generalization
- Promotion decision: extreme_reset_sparse_not_source_positive
- Decision reason: M704 generates 5120 scenarios and 2048 matched pairs with 27 reset-history-critical accepted rows across 5 fault families but 0 wrong-history-critical rows so source export PPO and promotion remain blocked

## Hypothesis

Extreme hidden-condition scenario generation will produce source-diverse rows where command-response history affects the safe evasive action.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m703-extreme-dynamics-scenario-corpus-design.md, docs/m702-boundary-sensitivity-scale-diagnostic-audit.md, runs/m701_boundary_sensitivity_scale_diagnostic/summary.json
- parent_config: experiments/manifests/m703-extreme-dynamics-scenario-corpus-design.json
- parent_objective: implement no-training extreme hidden-condition scenario corpus
- derived_from: m703-extreme-dynamics-scenario-corpus-design
- blocked_by: m703-extreme-dynamics-scenario-corpus-design
- supersedes: None
- invalidates: None

## Success Criteria

- summary.json is written
- scenario_summary.csv is written
- fault_family_summary.csv is written
- severity_summary.csv is written
- matched_hidden_condition_pairs.csv is written
- accepted_rows.csv is written
- rejected_rows.csv is written
- model_fidelity_limits.md is written
- actor checksum unchanged
- no objective actor update PPO or promotion

## Failure Criteria

- implementation mutates or trains actor
- implementation adds hidden fault labels to actor input
- implementation omits model-fidelity limits
- implementation omits matched hidden-condition criteria
- implementation admits objective design without source-positive audit

## Evidence Gates

- implementation writes fault family severity and scenario artifacts
- implementation keeps hidden fault labels out of actor input
- implementation separates current-model faults from future four-wheel-only faults
- implementation reports matched hidden-condition rows
- implementation reports history-action-critical rows
- actor checksum unchanged
- no objective actor update PPO or promotion occurs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor
- do not run PPO
- do not promote a checkpoint
- do not change actor observation shape
- do not add fault labels to actor input
- do not call single-track proxies true single-wheel faults
- do not export corpus before source-positive audit

## Failure Taxonomy

- none

## Scoreboard

- milestone: m704-extreme-dynamics-scenario-corpus-implementation
- type: infrastructure
- checkpoint: runs/m704_extreme_dynamics_scenario_corpus/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: extreme_reset_sparse_not_source_positive
- reason: M704 generates 5120 scenarios and 2048 matched pairs with 27 reset-history-critical accepted rows across 5 fault families but 0 wrong-history-critical rows so source export PPO and promotion remain blocked

## Next Blocker

m705-extreme-dynamics-scenario-corpus-audit
