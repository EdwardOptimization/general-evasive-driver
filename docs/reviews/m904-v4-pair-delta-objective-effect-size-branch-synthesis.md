# m904-v4-pair-delta-objective-effect-size-branch-synthesis Research Review

## Summary

- Generated at UTC: 20260525T204227Z
- Type: gate
- Gate tier: process
- Promotion decision: not_applicable
- Decision reason: M904 may only synthesize the M895-M903 branch and choose the next branch. It must not run benchmark, train, run PPO, or promote.

## Hypothesis

M895-M903 have enough margin-only public evidence to close the effect-size branch and choose a next branch, while keeping success-improvement, PPO, and promotion claims blocked.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt, runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/raw_candidate.pt, runs/m891_v4_enriched_pair_delta_objective_only_repeat_seed10887/checkpoints/raw_candidate.pt
- parent_dataset: docs/m895-v4-pair-delta-objective-effect-size-budget-audit.md, docs/m896-v4-pair-delta-controlled-scaling-replay-design.md, docs/m897-v4-pair-delta-raw-candidate-controlled-scaling-gate.md, docs/m898-v4-pair-delta-raw-scaling-gate-audit.md, docs/m899-v4-pair-delta-raw-scaling-fresh-generalization-design.md, docs/m900-v4-pair-delta-raw-scaling-fresh-generalization-benchmark.md, docs/m901-v4-pair-delta-raw-scaling-fresh-result-audit.md, docs/m902-v4-pair-delta-raw-scaling-challenge-generalization-design.md, docs/m903-v4-pair-delta-raw-scaling-challenge-generalization-benchmark.md
- parent_config: experiments/manifests/m903-v4-pair-delta-raw-scaling-challenge-generalization-benchmark.json
- parent_objective: synthesize M895-M903 objective-effect-size branch before integration, PPO, or further scenario-family work
- derived_from: m903-v4-pair-delta-raw-scaling-challenge-generalization-benchmark
- blocked_by: M895-M903 reached branch cadence after raw scaling passed public proof, fresh, and challenge margin gates
- supersedes: None
- invalidates: None

## Success Criteria

- M904 writes a synthesis document covering M895-M903
- M904 answers required synthesis questions
- M904 records proof/fresh/challenge evidence and caveats
- M904 chooses the next branch
- M904 keeps PPO and promotion blocked

## Failure Criteria

- M904 runs benchmark or training
- M904 admits PPO or promotion
- M904 treats margin-only evidence as success improvement
- M904 omits public overfit risk
- M904 skips next-branch decision

## Evidence Gates

- M904 must synthesize M895-M903
- M904 must separate margin-only evidence from success improvement
- M904 must decide next branch before integration, PPO, or more scenario work
- M904 must record public-gate overfit risk
- M904 must keep promotion blocked

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not run benchmark in M904
- do not train actor or residual parameters
- do not run PPO
- do not promote a checkpoint
- do not claim private holdout generalization
- do not skip synthesis before next branch

## Failure Taxonomy

- metric_artifact
- objective_overfit
- behavior_regression
- proof_washout
- scenario_sampling_failure
- contract_violation
- lineage_invalid

## Scoreboard

- No scoreboard row recorded.

## Next Blocker

M895-M903 effect-size branch synthesis has not yet been written
