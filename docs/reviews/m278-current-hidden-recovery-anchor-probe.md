# m278-current-hidden-recovery-anchor-probe Research Review

## Summary

- Generated at UTC: 20260522T183248Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: admit_recovery_anchored_actor_update
- Decision reason: M278 exports a validated 30-row current-hidden recovery anchor; all fragile rows recover and row16 margin improves from 0.000000636 to 0.000562819 without PPO

## Hypothesis

A local first-action override evaluated under the current M272 hidden state can recover terminal-margin slack for row16 without cross-checkpoint hidden leakage.

## Lineage

- parent_checkpoint: runs/m272_m264_to_m271_interpolation_boundary/checkpoints/alpha_0_01025.pt
- parent_dataset: runs/m275_terminal_margin_retention_surface/terminal_margin_registry.csv, runs/m276_m183_m170_row16_gate_seed9510/boundary_replay_rows.csv
- parent_config: experiments/manifests/m277-terminal-margin-recovery-anchor-design.json, docs/m277-terminal-margin-recovery-anchor-design.md
- parent_objective: current-hidden local-action recovery anchor probe
- derived_from: m277-terminal-margin-recovery-anchor-design
- blocked_by: m277-terminal-margin-recovery-anchor-design
- supersedes: None
- invalidates: None

## Success Criteria

- row16 is probed with current M272 observation and hidden
- candidate overrides are evaluated by simulator terminal margin
- recovery_anchor.npz exports at least one recovered row or the failure is documented
- exported NPZ loads through the existing trajectory anchor loader
- no PPO or actor update is run

## Failure Criteria

- row16 is not probed
- source checkpoint hidden states are used as current actor input
- no action improves row16 and the failure is not documented
- PPO or actor update is run

## Evidence Gates

- probe local first-action overrides on current hidden states
- export recovery_anchor.npz if at least row16 recovers
- validate TrajectoryActionAnchor NPZ shape contract
- do not run PPO

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in M278
- do not run a new actor update in M278
- do not use old checkpoint hidden states
- do not loosen row16 terminal-margin floor
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m278-current-hidden-recovery-anchor-probe
- type: infrastructure
- checkpoint: not_applicable_infrastructure_task
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_recovery_anchored_actor_update
- reason: M278 exports a validated 30-row current-hidden recovery anchor; all fragile rows recover and row16 margin improves from 0.000000636 to 0.000562819 without PPO

## Next Blocker

m279-recovery-anchored-actor-update
