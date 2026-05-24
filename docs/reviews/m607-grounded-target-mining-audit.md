# m607-grounded-target-mining-audit Research Review

## Summary

- Generated at UTC: 20260524T084931Z
- Type: gate
- Gate tier: process
- Promotion decision: grounded_target_mining_audit_admit_boundary_conditioned_source_design
- Decision reason: M607 classifies M606 zero-accepted targets as primarily source-row boundary-distance with secondary first-action locality; threshold artifact is not primary and training remains blocked

## Hypothesis

M606 zero-accepted targets should be audited before any optimizer step; the audit should identify whether the blocker is source-row boundary distance, first-action search locality, thresholds, or non-actionable belief movement.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m604_guarded_capability_action_coupling_evaluator/coupling_rows.csv, runs/m606_grounded_capability_action_target_miner/target_candidates.csv, runs/m606_grounded_capability_action_target_miner/unaccepted_rows.csv, runs/m606_grounded_capability_action_target_miner/summary.json
- parent_config: experiments/manifests/m606-grounded-capability-action-target-miner-implementation.json, docs/m605-grounded-capability-action-target-mining-design.md
- parent_objective: audit zero-accepted grounded target mining result before changing search or optimizer scope
- derived_from: m606-grounded-capability-action-target-miner-implementation
- blocked_by: m606-grounded-capability-action-target-miner-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- audit summarizes candidate margin and risk improvement distributions
- audit classifies the zero-accepted result without changing thresholds retroactively
- audit chooses exactly one next branch: wider grounded search, source re-mining, or abandon this target branch
- actor training PPO and promotion remain blocked
- research validation passes

## Failure Criteria

- audit treats zero accepted targets as successful action labels
- audit changes thresholds and reinterprets M606 as accepted
- audit starts training or PPO
- audit promotes a checkpoint
- audit omits unaccepted rows

## Evidence Gates

- audit why no targets were accepted
- separate threshold issue from boundary-distance issue
- decide whether to widen search horizon/grid or re-mine source rows
- keep actor training and PPO blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote checkpoint
- do not lower thresholds after seeing results and call the same run accepted
- do not use M604 belief-only gaps as action labels
- do not add privileged actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m607-grounded-target-mining-audit
- type: gate
- checkpoint: docs/m607-grounded-target-mining-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: grounded_target_mining_audit_admit_boundary_conditioned_source_design
- reason: M607 classifies M606 zero-accepted targets as primarily source-row boundary-distance with secondary first-action locality; threshold artifact is not primary and training remains blocked

## Next Blocker

m608-grounded-target-search-escalation-design
