# m872-v4-boundary-preserving-missing-seed-pair-delta-refresh-design Research Review

## Summary

- Generated at UTC: 20260525T181643Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: not_applicable
- Decision reason: M872 may only design a no-training normal-boundary-preserving refresh. It must not run replay, train, promote, or admit objective conversion.

## Hypothesis

A boundary-preserving design can address M870's actual failure mode by first finding missing-seed retargets whose normal branch stays inside the accepted margin window, then replaying pair-delta sequences only on those rows.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m871-v4-generated-boundary-pair-delta-coverage-expansion-audit.md, docs/m870-v4-generated-boundary-pair-delta-coverage-expansion-implementation.md, runs/m870_v4_generated_boundary_pair_delta_coverage_expansion/summary.json, runs/m870_v4_generated_boundary_pair_delta_coverage_expansion/pair_delta_sequence_rows.csv, runs/m870_v4_generated_boundary_pair_delta_coverage_expansion/target_weak_seed_rows.csv, runs/m870_v4_generated_boundary_pair_delta_coverage_expansion/retarget_candidate_rows.csv
- parent_config: experiments/manifests/m871-v4-generated-boundary-pair-delta-coverage-expansion-audit.json
- parent_objective: design boundary-preserving missing-seed refresh after M870 retarget grid missed accepted normal-margin window
- derived_from: m871-v4-generated-boundary-pair-delta-coverage-expansion-audit
- blocked_by: M870 retarget replay produced zero rows with accepted normal branch window despite nonzero outcome sensitivity
- supersedes: None
- invalidates: None

## Success Criteria

- M872 designs normal-branch boundary search or refinement for missing seeds 78048 78055 and 78057
- M872 defines separate artifacts for normal-boundary candidate rows and pair-delta sequence outcome rows
- M872 keeps primary accepted thresholds unchanged
- M872 defines component controls as diagnostic-only
- M872 decides whether implementation is allowed before branch synthesis

## Failure Criteria

- M872 runs replay or training
- M872 admits objective conversion from M870 rows
- M872 lowers accepted thresholds
- M872 skips the normal-window bracketing issue
- M872 ignores workflow synthesis cadence

## Evidence Gates

- M872 must be design-only
- M872 must preserve no-training no-PPO no-promotion discipline
- M872 must explicitly separate normal-boundary bracketing from pair-delta outcome replay
- M872 must keep accepted-row thresholds unchanged
- M872 must include branch-synthesis fallback because cadence is near

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not train actor parameters
- do not train M761 residual-head parameters
- do not run PPO
- do not promote a checkpoint
- do not lower accepted-row thresholds
- do not count colliding-normal rows as accepted pair-delta evidence
- do not merge normal-boundary search and pair-delta evidence without separate artifacts

## Failure Taxonomy

- scenario_sampling_failure
- metric_artifact
- contract_violation

## Scoreboard

- No scoreboard row recorded.

## Next Blocker

Boundary-preserving missing-seed refresh has not yet been designed
