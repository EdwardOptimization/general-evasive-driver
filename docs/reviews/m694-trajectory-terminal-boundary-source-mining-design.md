# m694-trajectory-terminal-boundary-source-mining-design Research Review

## Summary

- Generated at UTC: 20260524T163243Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: trajectory_terminal_boundary_source_mining_design_admit_m695
- Decision reason: M694 designs a closed-loop terminal-margin sensitivity miner that rejects normal-failed rows enforces source diversity and blocks actor update PPO promotion

## Hypothesis

A trajectory/terminal-boundary source miner can define a better source surface than M671/M689 by selecting rows where small first-action perturbations or counterfactual histories measurably affect terminal margin, risk, collision, or recovery.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m693-gate-margin-closed-loop-replay-audit.md, runs/m692_gate_margin_closed_loop_replay/summary.json, runs/m692_gate_margin_closed_loop_replay/replay_rows.csv
- parent_config: experiments/manifests/m693-gate-margin-closed-loop-replay-audit.json
- parent_objective: design trajectory and terminal-margin sensitive source mining after response-amplification pivot
- derived_from: m693-gate-margin-closed-loop-replay-audit
- blocked_by: m693-gate-margin-closed-loop-replay-audit
- supersedes: None
- invalidates: further response_amplification_actor_coupling milestones without a new replay-positive source surface

## Success Criteria

- design identifies candidate source artifacts and scenario configs
- design defines terminal-margin sensitivity metrics
- design defines normal-success or near-boundary filters
- design defines wrong/counterfactual-history outcome tests
- design defines source-diversity and heldout split rules
- design defines negative-result interpretations
- actor update PPO and promotion remain blocked

## Failure Criteria

- design accepts output-only residual metrics as sufficient
- design cannot distinguish normal-failed from action-critical rows
- design omits terminal-margin or risk sensitivity metrics
- design omits source-diversity rules
- design admits actor update or PPO before mining

## Evidence Gates

- design defines terminal-margin sensitivity before objective training
- design distinguishes normal-failed rows from action-critical rows
- design includes source-diversity rules
- design blocks actor update PPO and promotion
- design keeps P0 human-view actor inputs unchanged

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor
- do not run PPO
- do not promote a checkpoint
- do not reuse exact output residual metrics as replay evidence
- do not accept rows that are already normal-failed as action-critical
- do not change actor observation inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m694-trajectory-terminal-boundary-source-mining-design
- type: infrastructure
- checkpoint: docs/m694-trajectory-terminal-boundary-source-mining-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: trajectory_terminal_boundary_source_mining_design_admit_m695
- reason: M694 designs a closed-loop terminal-margin sensitivity miner that rejects normal-failed rows enforces source diversity and blocks actor update PPO promotion

## Next Blocker

m695-trajectory-terminal-boundary-source-miner-implementation
