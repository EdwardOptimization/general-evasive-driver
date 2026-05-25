# m869-v4-generated-boundary-pair-delta-coverage-expansion-design Research Review

## Summary

- Generated at UTC: 20260525T174642Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: not_applicable
- Decision reason: M869 may only design the next no-training accepted pair-delta coverage expansion. It must not replay, train, run PPO, promote, or claim learned self-ID.

## Hypothesis

A targeted no-training coverage-expansion design can address M867's accepted pair-delta seed/direction/axis concentration before objective training.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m868-v4-generated-boundary-pair-delta-refresh-audit.md, runs/m867_v4_generated_boundary_pair_delta_refresh/summary.json, runs/m867_v4_generated_boundary_pair_delta_refresh/pair_delta_sequence_rows.csv, runs/m867_v4_generated_boundary_pair_delta_refresh/accepted_pair_delta_rows.csv, runs/m867_v4_generated_boundary_pair_delta_refresh/balanced_pair_delta_rows.csv, runs/m867_v4_generated_boundary_pair_delta_refresh/diversity_summary.json
- parent_config: experiments/manifests/m868-v4-generated-boundary-pair-delta-refresh-audit.json
- parent_objective: design targeted no-training expansion for accepted pair-delta coverage
- derived_from: m868-v4-generated-boundary-pair-delta-refresh-audit
- blocked_by: M867 accepted pair-delta rows are concentrated in two left seeds and pair_delta_negative/lateral-offset axes
- supersedes: None
- invalidates: None

## Success Criteria

- M869 writes a design document for accepted pair-delta coverage expansion
- M869 names target gaps from M867: missing accepted seeds 78048 78055 78057, direction dominance, and axis dominance
- M869 defines source-aware gates for the next implementation
- M869 keeps component controls diagnostic-only
- M869 keeps objective training PPO and promotion blocked

## Failure Criteria

- M869 runs replay
- M869 trains actor or residual-head parameters
- M869 runs PPO
- M869 promotes a checkpoint
- M869 treats pairability projection or component controls as primary pair-delta outcome evidence

## Evidence Gates

- M869 must be design-only
- M869 must target accepted pair-delta coverage rather than raw pairability projection
- M869 must keep component controls diagnostic-only
- M869 must preserve actor and residual-head mutation blocks
- M869 must keep objective training PPO and promotion blocked

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not run replay in M869
- do not train actor parameters
- do not train M761 residual-head parameters
- do not run PPO
- do not promote a checkpoint
- do not treat component-control rows as primary pair-delta evidence
- do not claim learned self-ID from diagnostic pair-delta coverage

## Failure Taxonomy

- scenario_sampling_failure
- metric_artifact
- contract_violation

## Scoreboard

- No scoreboard row recorded.

## Next Blocker

M867 accepted pair-delta coverage concentration has not yet been addressed by a targeted expansion design
