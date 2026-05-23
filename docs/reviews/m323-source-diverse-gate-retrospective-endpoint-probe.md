# m323-source-diverse-gate-retrospective-endpoint-probe Research Review

## Summary

- Generated at UTC: 20260523T061836Z
- Type: gate
- Gate tier: proof
- Promotion decision: admit_m324_single_key_window_override_policy_design
- Decision reason: M323 shows M316 repaired endpoint passes 2 of 2 source-diverse protected gates with 17 of 17 drops but old 9944 sweep remains singleton-window failure

## Hypothesis

The repaired M316 endpoint may fail the old saturated 9944 key while still preserving the refreshed M320 source-diverse protected surface, clarifying whether future acceptance can rely on the multi-surface gate plus explicit singleton-window audit.

## Lineage

- parent_checkpoint: runs/m316_m314_to_repaired_protected_key_bounded_interpolation/checkpoints/alpha_0_0025.pt, runs/m316_exact_repair_from_raw_s40_seed10096/candidate_checkpoint.pt
- parent_dataset: runs/m320_m316_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv, runs/m320_m314_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv, runs/m320_m316_repaired_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv
- parent_config: experiments/manifests/m322-source-diverse-protected-gate-implementation.json, docs/m322-source-diverse-protected-gate-implementation.md
- parent_objective: diagnose whether the M316 repaired endpoint passes the new source-diverse protected gate even though old 9944 is saturated
- derived_from: m322-source-diverse-protected-gate-implementation
- blocked_by: m322-source-diverse-protected-gate-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- source-diverse wrapper run completes
- all M320 replay gates report pass or failures are classified
- 9944 diagnostic is recorded
- decision is diagnostic only, not promotion
- no PPO is run

## Failure Criteria

- wrapper cannot evaluate the endpoint
- source-diverse proof rows fail broadly
- M323 promotes a checkpoint
- M323 changes actor inputs

## Evidence Gates

- run source-diverse protected wrapper on M316 repaired endpoint as candidate
- ingest old 9944 diagnostic
- do not promote a checkpoint
- classify whether old-key failure is singleton-window-only or source-diverse proof failure
- do not run PPO

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not promote M316 repaired in M323
- do not ignore 9944 diagnostic
- do not change actor inputs
- do not tune from private holdouts

## Failure Taxonomy

- none

## Scoreboard

- milestone: m323-source-diverse-gate-retrospective-endpoint-probe
- type: gate
- checkpoint: runs/m316_exact_repair_from_raw_s40_seed10096/candidate_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m324_single_key_window_override_policy_design
- reason: M323 shows M316 repaired endpoint passes 2 of 2 source-diverse protected gates with 17 of 17 drops but old 9944 sweep remains singleton-window failure

## Next Blocker

m324-single-key-window-override-policy-design
