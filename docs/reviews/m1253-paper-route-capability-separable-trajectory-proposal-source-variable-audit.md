# m1253-paper-route-capability-separable-trajectory-proposal-source-variable-audit Research Review

## Summary

- Generated at UTC: 20260528T110125Z
- Type: gate
- Gate tier: process
- Promotion decision: trajectory_proposal_source_near_miss_stop_same_budget_pivot_to_event_timing_source_design
- Decision reason: M1253 audits M1250-M1252 near-miss negatives and pivots from same proposal budget to event-timing/source-state source design

## Hypothesis

M1250-M1252 indicate a source-state/timing or model-fidelity bottleneck rather than a reason to continue expanding the same proposal budget.

## Lineage

- parent_checkpoint: runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt
- parent_dataset: docs/m1252-paper-route-capability-separable-proposal-margin-restoration-smoke.md, runs/m1252_capability_separable_proposal_margin_restoration_smoke/summary.json, runs/m1252_capability_separable_proposal_margin_restoration_smoke/matched_capability_pairs.csv
- parent_config: experiments/manifests/m1252-paper-route-capability-separable-proposal-margin-restoration-smoke.json
- parent_objective: audit trajectory proposal source variable after targeted margin-restoration remains zero-accepted
- derived_from: m1252-paper-route-capability-separable-proposal-margin-restoration-smoke
- blocked_by: M1252 improved the near-miss but still produced zero accepted separable rows
- supersedes: another immediate proposal-budget or seed expansion on the same public source
- invalidates: None

## Success Criteria

- docs/m1253-paper-route-capability-separable-trajectory-proposal-source-variable-audit.md exists
- audit cites M1250 and M1252 near-miss metrics
- audit does not lower thresholds
- audit chooses the next branch
- no training, PPO, promotion, private holdout, or actor-input expansion occurs

## Failure Criteria

- audit is missing
- audit ignores M1252 stop rule
- audit proposes another budget expansion without a new evidence variable
- training, PPO, private holdout, promotion, or actor-input expansion occurs

## Evidence Gates

- M1253 must preserve actor input contract
- M1253 must not train controllers
- M1253 must not run PPO
- M1253 must not use private holdout
- M1253 must not promote
- M1253 must decide whether to continue trajectory proposal source, pivot source state/timing, or move to fidelity/teacher source

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not promote
- do not add hidden parameters, proposal labels, oracle outcomes, or search outputs to actor inputs
- do not lower source-positive thresholds
- do not start another source run before audit

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m1253-paper-route-capability-separable-trajectory-proposal-source-variable-audit
- type: gate
- checkpoint: docs/m1253-paper-route-capability-separable-trajectory-proposal-source-variable-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: trajectory_proposal_source_near_miss_stop_same_budget_pivot_to_event_timing_source_design
- reason: M1253 audits M1250-M1252 near-miss negatives and pivots from same proposal budget to event-timing/source-state source design

## Next Blocker

m1254-paper-route-capability-separable-event-timing-source-design
