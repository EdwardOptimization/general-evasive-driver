# m1184-paper-route-gate-utility-audit-design Research Review

## Summary

- Generated at UTC: 20260528T040112Z
- Type: gate
- Gate tier: process
- Promotion decision: paper_route_gate_utility_audit_design_admit_matrix_run
- Decision reason: M1184 designs candidate classes gate stacks utility metrics and provisional classifications for historical gate cleanup and pre-registers M1185 without replay training PPO promotion private holdout or actor-input change

## Hypothesis

A pre-registered gate utility audit can determine which historical gates and repair tools are core, research-only, extended-regression, legacy, or deprecated before the paper route proceeds to broad training or gate cleanup.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/paper-route-finite-window-vs-gru-plan.md, docs/m1183-v4-public-base-no-residual-source-rich-smoke-run.md, runs/m1183_current_base_no_residual_source_rich_smoke/summary.json
- parent_config: experiments/manifests/m1183-v4-public-base-no-residual-source-rich-smoke-run.json
- parent_objective: design a gate utility audit that classifies existing gates and historical repair logic before future training or paper claims
- derived_from: m1182a-v4-public-base-paper-route-finite-window-gru-plan, m1183-v4-public-base-no-residual-source-rich-smoke-run
- blocked_by: historical gates and row-specific repair logic may over-constrain the paper route without utility evidence
- supersedes: using full historical gate stack as an unaudited permanent active blocker
- invalidates: demoting or deleting gates without a candidate-based utility audit, continuing broad training before deciding which gates are core versus legacy

## Success Criteria

- gate utility audit design exists
- candidate classes include good, known bad, near-miss, and no-op candidates
- gate stacks A/B/C are specified
- classification rules are specified
- follow-up utility matrix run is pre-registered
- no gate demotion, candidate replay, actor training, PPO, promotion, private holdout, or actor-input change occurs

## Failure Criteria

- design demotes gates without evidence
- design omits known bad candidates
- design lacks keep/demote/deprecate rules
- candidate replay, gate demotion, actor training, PPO, promotion, private holdout, or actor-input change starts

## Evidence Gates

- M1184 may design the gate utility audit only
- M1184 must not run candidate replay
- M1184 must not demote or delete gates
- M1184 must not train actor weights
- M1184 must not run PPO
- M1184 must not promote
- M1184 must not use private holdout
- M1184 must not change actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run candidate replay
- do not demote gates without evidence
- do not delete historical tools
- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not change actor inputs
- do not claim paper evidence from design-only work

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1184-paper-route-gate-utility-audit-design
- type: gate
- checkpoint: docs/m1184-paper-route-gate-utility-audit-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: paper_route_gate_utility_audit_design_admit_matrix_run
- reason: M1184 designs candidate classes gate stacks utility metrics and provisional classifications for historical gate cleanup and pre-registers M1185 without replay training PPO promotion private holdout or actor-input change

## Next Blocker

m1185-paper-route-gate-utility-matrix-run
