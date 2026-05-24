# m608-boundary-conditioned-grounded-source-design Research Review

## Summary

- Generated at UTC: 20260524T085149Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: boundary_conditioned_grounded_source_design_admit_m609
- Decision reason: M608 designs full-pool boundary/risk source screening with baseline continuation diversity thresholds and branch preservation before rerunning grounded target mining

## Hypothesis

Grounded action targets require source rows that are already near a behaviorally meaningful margin/risk boundary; M608 should design that boundary-conditioned source screen before rerunning target mining.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m604_guarded_capability_action_coupling_evaluator/coupling_rows.csv, runs/m606_grounded_capability_action_target_miner/target_candidates.csv, runs/m606_grounded_capability_action_target_miner/unaccepted_rows.csv, docs/m607-grounded-target-mining-audit.md
- parent_config: experiments/manifests/m607-grounded-target-mining-audit.json, docs/m605-grounded-capability-action-target-mining-design.md
- parent_objective: design boundary/risk-conditioned source selection before another grounded target miner run
- derived_from: m607-grounded-target-mining-audit
- blocked_by: m607-grounded-target-mining-audit
- supersedes: None
- invalidates: None

## Success Criteria

- design specifies boundary margin and risk windows
- design specifies how to preserve source diversity
- design specifies how to avoid using labels as actor inputs
- design specifies next implementation artifacts and pass/fail criteria
- research validation passes

## Failure Criteria

- design starts training
- design uses M604 belief-only gaps directly as action labels
- design ignores M606 zero-accepted evidence
- design permits threshold retrofitting
- design promotes a checkpoint

## Evidence Gates

- define boundary/risk source-screen metrics
- define source-diversity thresholds
- define normal/variant branch preservation requirements
- define when to rerun local target mining
- keep actor training and PPO blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train in design milestone
- do not run PPO
- do not promote checkpoint
- do not reuse M606 zero-accepted rows as labels
- do not lower M606 thresholds retroactively
- do not add privileged actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m608-boundary-conditioned-grounded-source-design
- type: infrastructure
- checkpoint: docs/m608-boundary-conditioned-grounded-source-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: boundary_conditioned_grounded_source_design_admit_m609
- reason: M608 designs full-pool boundary/risk source screening with baseline continuation diversity thresholds and branch preservation before rerunning grounded target mining

## Next Blocker

m609-boundary-conditioned-source-miner-implementation
