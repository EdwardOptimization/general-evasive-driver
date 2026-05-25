# m876-v4-pair-delta-corpus-dedup-resplit-design Research Review

## Summary

- Generated at UTC: 20260525T183559Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: not_applicable
- Decision reason: M876 may only design no-training dedup/resplit. It must not train, run PPO, promote, or admit objective design directly.

## Hypothesis

A no-training dedup/resplit design can convert M873's positive but duplicate-heavy corpus into a cleaner objective-readiness candidate without actor updates.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m875-v4-pair-delta-objective-readiness-audit.md, runs/m873_v4_boundary_preserving_missing_seed_pair_delta_refresh/new_accepted_pair_delta_rows.csv, runs/m873_v4_boundary_preserving_missing_seed_pair_delta_refresh/balanced_pair_delta_rows.csv, runs/m873_v4_boundary_preserving_missing_seed_pair_delta_refresh/train_public_rows.csv, runs/m873_v4_boundary_preserving_missing_seed_pair_delta_refresh/eval_public_rows.csv, runs/m873_v4_boundary_preserving_missing_seed_pair_delta_refresh/source_holdout_public_rows.csv
- parent_config: experiments/manifests/m875-v4-pair-delta-objective-readiness-audit.json
- parent_objective: design no-training dedup and resplit before objective design
- derived_from: m875-v4-pair-delta-objective-readiness-audit
- blocked_by: M875 found duplicate pressure and a split where train and holdout contain zero new M873 rows
- supersedes: None
- invalidates: None

## Success Criteria

- M876 defines closed-loop signature or geometry dedup keys
- M876 defines transformed train/eval/holdout split policy
- M876 preserves existing and new evidence distinctions
- M876 keeps 78055 caveat explicit
- M876 pre-registers implementation only if objective design remains blocked

## Failure Criteria

- M876 trains actor or residual-head parameters
- M876 runs PPO
- M876 promotes a checkpoint
- M876 designs an objective without dedup
- M876 hides duplicate pressure or 78055 caveat

## Evidence Gates

- M876 must be design-only
- M876 must design deduplication before objective work
- M876 must design source-aware splits with explicit purpose
- M876 must keep the 78055 caveat visible
- M876 must keep objective training PPO and promotion blocked

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not train actor parameters
- do not train M761 residual-head parameters
- do not run PPO
- do not promote a checkpoint
- do not treat duplicate axis labels as independent samples
- do not hide 78055 caveat
- do not perform objective design before dedup/resplit audit

## Failure Taxonomy

- objective_overfit
- scenario_sampling_failure
- metric_artifact
- contract_violation

## Scoreboard

- No scoreboard row recorded.

## Next Blocker

Pair-delta corpus dedup/resplit has not yet been designed
