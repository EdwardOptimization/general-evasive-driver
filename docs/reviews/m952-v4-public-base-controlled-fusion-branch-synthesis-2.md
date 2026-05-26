# m952-v4-public-base-controlled-fusion-branch-synthesis-2 Research Review

## Summary

- Generated at UTC: 20260526T003155Z
- Type: gate
- Gate tier: process
- Promotion decision: pivot_to_replay_constrained_target_feasibility
- Decision reason: M952 synthesizes M942-M951 and pivots away from local controlled-fusion retuning to no-training replay-constrained target feasibility before more actor updates

## Hypothesis

The controlled-fusion local objective branch has enough evidence to decide whether to stop local retuning and pivot to a new branch.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt, runs/m951_v4_public_base_rejected_branch_boundary_retune_probe/checkpoints/raw_rejected_branch_retention_update.pt
- parent_dataset: docs/m941-v4-public-base-controlled-fusion-branch-synthesis.md, docs/m942-v4-public-base-controlled-fusion-micro-boundary-audit.md, docs/m944-v4-public-base-controlled-fusion-candidate-compatibility-implementation.md, docs/m946-v4-public-base-controlled-fusion-candidate-replay-gate-implementation.md, docs/m947-v4-public-base-controlled-fusion-candidate-failing-surface-audit.md, docs/m949-v4-public-base-controlled-fusion-rejected-branch-retention-probe.md, docs/m951-v4-public-base-rejected-branch-boundary-retune-probe.md, runs/m951_v4_public_base_rejected_branch_boundary_retune_probe/summary.json
- parent_config: experiments/manifests/m951-v4-public-base-rejected-branch-boundary-retune-probe.json
- parent_objective: synthesize controlled-fusion evidence after exact-compatible candidates and rejected-branch retune both fail promotion-level overlap
- derived_from: m941-v4-public-base-controlled-fusion-branch-synthesis, m951-v4-public-base-rejected-branch-boundary-retune-probe
- blocked_by: M951 used the one allowed local retune and still produced zero candidate alphas
- supersedes: None
- invalidates: additional local coefficient tweaks on the same controlled-fusion objective before synthesis

## Success Criteria

- synthesis document exists
- M942-M951 evidence is summarized
- supported and falsified claims are recorded
- failure taxonomy is recorded
- next branch decision is recorded
- training, replay, PPO, and promotion are blocked

## Failure Criteria

- M952 omits synthesis questions
- M952 admits another local retune without synthesis
- M952 runs training, full replay, PPO, or promotion
- M952 does not choose the next blocker

## Evidence Gates

- M952 must synthesize M942-M951 evidence
- M952 must list supported and falsified claims
- M952 must classify failure taxonomy
- M952 must decide whether to stop, pivot, or open a new branch
- M952 must block training, replay, PPO, and promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run another local retune
- do not train in M952
- do not run full replay
- do not run PPO
- do not promote
- do not open encoders or GRU without an explicit synthesis decision

## Failure Taxonomy

- promotion_gate_failure
- objective_overfit

## Scoreboard

- milestone: m952-v4-public-base-controlled-fusion-branch-synthesis-2
- type: gate
- checkpoint: docs/m952-v4-public-base-controlled-fusion-branch-synthesis-2.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: pivot_to_replay_constrained_target_feasibility
- reason: M952 synthesizes M942-M951 and pivots away from local controlled-fusion retuning to no-training replay-constrained target feasibility before more actor updates

## Next Blocker

m953-v4-public-base-replay-constrained-target-feasibility-design
