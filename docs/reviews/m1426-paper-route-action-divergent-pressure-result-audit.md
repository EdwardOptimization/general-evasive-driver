# m1426-paper-route-action-divergent-pressure-result-audit Research Review

## Summary

- Generated at UTC: 20260529T021457Z
- Type: gate
- Gate tier: process
- Promotion decision: action_divergent_pressure_audit_admit_bounded_relocation_replay_design
- Decision reason: M1426 classifies M1425 as source-diverse but shared-margin-proxy limited and admits design-only bounded relocation replay route

## Hypothesis

M1425's zero history-positive result is likely caused by near-zero terminal margin gaps under a shared-margin proxy, so the next route must be audited before any replay or training.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1425_action_divergent_outcome_pressure_source_smoke/summary.json, docs/m1425-paper-route-action-divergent-outcome-pressure-source-smoke.md
- parent_config: experiments/manifests/m1425-paper-route-action-divergent-outcome-pressure-source-smoke.json
- parent_objective: audit zero history-positive proxy result before any replay or training
- derived_from: m1425-paper-route-action-divergent-outcome-pressure-source-smoke
- blocked_by: M1425 found source-diverse action and pressure rows but zero history-positive proxy rows
- supersedes: lowering M1425 margin-gap threshold after seeing the result, direct replay without auditing proxy failure mode, training from proxy rows
- invalidates: None

## Success Criteria

- docs/m1426-paper-route-action-divergent-pressure-result-audit.md exists
- audit explains M1425 candidate pressure and history-positive counts
- audit classifies whether M1425 is source-limited proxy-limited or branch-limited
- audit chooses a non-training next route or stop decision
- audit does not run replay training PPO promotion private holdout corpus export or actor-input changes

## Failure Criteria

- audit document is missing
- audit lowers thresholds after seeing M1425 to reclassify the result as positive
- audit routes directly to training PPO promotion private holdout corpus export or claim expansion
- audit ignores proxy-only and requires-replay flags

## Evidence Gates

- M1426 must classify the M1425 negative result before any replay or training
- M1426 must decide whether to route to bounded relocation replay, constructor redesign, branch synthesis, or stop
- M1426 must not train run PPO promote use private holdout export corpus or change actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run closed-loop replay
- do not run outcome interventions
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export a training corpus
- do not lower the margin-gap threshold to pass after seeing M1425
- do not claim proxy rows as closed-loop evidence

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m1426-paper-route-action-divergent-pressure-result-audit
- type: gate
- checkpoint: docs/m1426-paper-route-action-divergent-pressure-result-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: action_divergent_pressure_audit_admit_bounded_relocation_replay_design
- reason: M1426 classifies M1425 as source-diverse but shared-margin-proxy limited and admits design-only bounded relocation replay route

## Next Blocker

m1427-paper-route-bounded-relocation-replay-design
