# m1185-paper-route-gate-utility-matrix-run Research Review

## Summary

- Generated at UTC: 20260528T040712Z
- Type: gate
- Gate tier: process
- Promotion decision: gate_utility_matrix_pass_route_to_active_gate_policy_design
- Decision reason: M1185 builds a 12-candidate 13-gate utility matrix from existing artifacts recommends Stack B as active public default and routes to active gate policy without replay training PPO promotion private holdout or actor-input change

## Hypothesis

Existing artifacts are sufficient to populate a first gate utility matrix that separates core, research-only, extended-regression, legacy, and deprecated gates without running replay or changing gates.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1184-paper-route-gate-utility-audit-design.md, docs/paper-route-finite-window-vs-gru-plan.md, experiments/scoreboard.csv, experiments/research_queue.csv, docs/current-status.md, docs/research-log.md
- parent_config: experiments/manifests/m1184-paper-route-gate-utility-audit-design.json
- parent_objective: build a gate utility matrix from existing artifacts so historical gates can be classified before cleanup
- derived_from: m1184-paper-route-gate-utility-audit-design
- blocked_by: gate cleanup and paper-route training need evidence about which gates catch known bad candidates and which gates false-reject good candidates
- supersedes: using an unaudited full historical gate stack as a permanent blocker, demoting row-specific gates without candidate-based utility evidence
- invalidates: claiming gate cleanup from a design-only milestone, using private holdout to tune gate classification, running replay or training inside the utility matrix milestone

## Success Criteria

- docs/m1185-paper-route-gate-utility-matrix-run.md exists
- docs/gate-utility-matrix.md exists
- summary.json exists
- candidate_manifest.csv exists
- gate_utility_matrix.csv exists
- gate_stack_decisions.csv exists
- candidate classes include good, known bad, near-miss, and null/no-op rows
- gate stacks A/B/C are represented
- gate classification recommendations are reported with reasons
- missing paths and not-applicable rows are explicit
- no gate demotion, candidate replay, actor training, PPO, promotion, private holdout, or actor-input change occurs

## Failure Criteria

- matrix demotes or deletes gates instead of recommending classifications
- known bad candidates are omitted
- good candidates are omitted
- missing paths are silently treated as pass or fail
- not-applicable rows are treated as driver passes or failures
- candidate replay, actor training, PPO, promotion, private holdout, or actor-input change starts

## Evidence Gates

- M1185 may inspect existing public artifacts, docs, manifests, and scoreboard rows
- M1185 must not run candidate replay
- M1185 must not demote or delete gates
- M1185 must not train actor weights
- M1185 must not run PPO
- M1185 must not promote
- M1185 must not use private holdout
- M1185 must not change actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run candidate replay
- do not demote or delete gates
- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not change actor inputs
- do not classify a missing-path candidate as pass or fail
- do not treat a not-applicable non-checkpoint artifact as a driver checkpoint
- do not claim paper evidence from matrix construction

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1185-paper-route-gate-utility-matrix-run
- type: gate
- checkpoint: runs/m1185_gate_utility_matrix/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: gate_utility_matrix_pass_route_to_active_gate_policy_design
- reason: M1185 builds a 12-candidate 13-gate utility matrix from existing artifacts recommends Stack B as active public default and routes to active gate policy without replay training PPO promotion private holdout or actor-input change

## Next Blocker

m1186-paper-route-active-gate-policy-design
