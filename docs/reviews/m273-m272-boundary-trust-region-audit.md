# m273-m272-boundary-trust-region-audit Research Review

## Summary

- Generated at UTC: 20260522T180407Z
- Type: gate
- Gate tier: proof
- Promotion decision: design_terminal_margin_retention_before_more_updates
- Decision reason: M273 classifies the M272 limiting row as a terminal-margin cliff where M183/M170 row16 flips between alpha 0.01025 and 0.0105 under microscopic action drift

## Hypothesis

M272's safe alpha is limited by a terminal-margin cliff on M183/M170 row 16; future learning needs a window-aware terminal-margin or trajectory-retention guard rather than another snippet-only actor update.

## Lineage

- parent_checkpoint: runs/m272_m264_to_m271_interpolation_boundary/checkpoints/alpha_0_01025.pt
- parent_dataset: runs/m272_boundary_m183_m170_replay_sweep/boundary_replay_rows.csv, runs/m272_selected_m183_m170_replay_gate/boundary_replay_rows.csv, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz
- parent_config: experiments/manifests/m272-m271-interpolation-retention-probe.json, docs/m272-m271-interpolation-retention-probe.md
- parent_objective: audit the M183/M170 row16 trust-region cliff before any new update or PPO
- derived_from: m272-m271-interpolation-retention-probe
- blocked_by: m272-m271-interpolation-retention-probe
- supersedes: None
- invalidates: None

## Success Criteria

- audit M183/M170 row16 at alpha 0.01025 and 0.0105
- quantify the action and margin movement that flips the row
- decide whether the next repair should be terminal-margin retention, trajectory anchor, or a stricter interpolation trust region
- produce a concrete M274 manifest recommendation
- no PPO or actor update is run

## Failure Criteria

- run PPO or a new actor update
- accept M271-style continuation without explaining the row16 cliff
- treat M272 promotion as evidence that PPO is safe
- change actor observation inputs

## Evidence Gates

- identify the limiting row and alpha boundary
- classify whether the failure is terminal-margin cliff, action drift, or hidden-state sensitivity
- design a retention objective before any actor update or PPO
- do not run PPO

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in M273
- do not run a new actor update in M273
- do not promote a new checkpoint
- do not loosen M183/M170 row16
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m273-m272-boundary-trust-region-audit
- type: gate
- checkpoint: runs/m272_m264_to_m271_interpolation_boundary/checkpoints/alpha_0_01025.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.844095
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: design_terminal_margin_retention_before_more_updates
- reason: M273 classifies the M272 limiting row as a terminal-margin cliff where M183/M170 row16 flips between alpha 0.01025 and 0.0105 under microscopic action drift

## Next Blocker

m274-terminal-margin-retention-design
