# m3228-c1-c5prime-oracle-demo-bc-warmstart Research Review

## Summary

- Generated at UTC: 20260612T042204Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: not_applicable
- Decision reason: Accept M3228 as completed C1 warm-start engineering only if the full preregistered demo+BC run passes all gates, writes checkpoint and dataset artifacts, and the result is documented and reviewed. BC rollout success is context only.

## Hypothesis

A pre-registered C1 C5-prime oracle-demo generator and behavior-cloning warm-start can replay structured A3 oracle rows, fit a held-out-selected BC checkpoint with DAgger-lite relabeling, and produce a Track-C warm-start artifact before validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof paper or self-ID claim.

## Lineage

- parent_checkpoint: docs/roadmap-phase3-codex-execution.md, docs/current-status.md, docs/m3222-a3-c5prime-target-consolidation.md, docs/m3227-d1-s4-hf-lite-chrono-pricing.md
- parent_dataset: runs/feasibility_audit/c5prime_target_consolidation/episode_rows.csv
- parent_config: experiments/feasibility_audit/c5prime_prereg.json, experiments/feasibility_audit/c5prime_c1_oracle_bc_prereg.json, scripts/feasibility_audit/c5prime_c1_oracle_bc_warmstart.py
- parent_objective: execute roadmap C1 after CP-1 conditional approval using the frozen current-sim C5-prime target only
- derived_from: M3222 A3 C5-prime target consolidation, CP-1 conditional approval on 2026-06-12, M3228 C1 quick smoke artifact
- blocked_by: C1 requires preregistered oracle-demo generation and held-out-selected BC warm-start before C2
- supersedes: the C1 OPEN status line if the full warm-start artifact, documentation, and review are completed
- invalidates: starting guarded RL without a frozen C1 demo and BC warm-start artifact, treating BC warm-start rollout success as validation or driver-performance evidence

## Success Criteria

- experiments/feasibility_audit/c5prime_c1_oracle_bc_prereg.json exists before full C1 rollout
- experiments/feasibility_audit/c5prime_c1_oracle_bc_warmstart_quick.json exists from the quick smoke
- experiments/feasibility_audit/c5prime_c1_oracle_bc_warmstart.json exists with protocol c5prime_c1_oracle_bc_warmstart
- full summary gates.all_passed is true
- full run writes a dataset NPZ and checkpoint PT under runs/feasibility_audit/c5prime_c1_oracle_bc_warmstart/full
- the result document separates measured artifacts from inferred interpretation

## Failure Criteria

- full C1 rollout starts without frozen preregistration
- a selected structured-oracle demo does not replay to success
- selection or validation role frames are used for BC training
- validation action-MSE gate fails
- the milestone runs PPO, mutates the incumbent, changes actor-input shape, or claims driver performance

## Evidence Gates

- M3228 must use a frozen C1 preregistration before full C1 rollout
- M3228 must select only structured A3 oracle rows from S1/S2/S3 T-limit target cells
- M3228 must keep selection and validation roles held out from BC training
- M3228 must use held-out epoch selection before reporting validation action MSE
- M3228 must write a checkpoint and dataset artifact
- M3228 must not run PPO, mutate ActiveSafetyReflexDriver, or make a driver-performance claim

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not touch ActiveSafetyReflexDriver
- do not invoke train_ppo or create a guarded-RL checkpoint
- do not use CEM-only A3 oracle rows because their action sequences were not persisted
- do not train on selection or validation role frames
- do not relax the validation action-MSE gate after seeing the result
- do not claim current-sim validation, high-fidelity sufficiency, promotion readiness, or self-ID

## Failure Taxonomy

- metric_artifact

## Scoreboard

- No scoreboard row recorded.

## Next Blocker

After C1, C2 guarded RL smoke is the next Track-C unit; C3 staged scale-up remains blocked on C2, D1b direction-positive, and CP-2.
