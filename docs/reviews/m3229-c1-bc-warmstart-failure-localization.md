# m3229-c1-bc-warmstart-failure-localization Research Review

## Summary

- Generated at UTC: 20260612T041257Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: manual_review
- Decision reason: no structured gates defined

## Hypothesis

A C1 BC warm-start failure-localization pass can decompose the failed M3228 preregistered action-MSE gate by role, level, oracle action, prefix/tail segment, and action channel before any revised C1 training validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof paper or self-ID claim.

## Lineage

- parent_checkpoint: experiments/feasibility_audit/c5prime_c1_oracle_bc_warmstart.json, runs/feasibility_audit/c5prime_c1_oracle_bc_warmstart/full/checkpoint.pt, docs/roadmap-phase3-codex-execution.md
- parent_dataset: runs/feasibility_audit/c5prime_c1_oracle_bc_warmstart/full/dataset.npz, runs/feasibility_audit/c5prime_target_consolidation/episode_rows.csv
- parent_config: experiments/feasibility_audit/c5prime_c1_oracle_bc_prereg.json, scripts/feasibility_audit/c5prime_c1_oracle_bc_warmstart.py, scripts/feasibility_audit/c5prime_c1_failure_localization.py
- parent_objective: localize the failed C1 warm-start gate without changing criteria or training a new model
- derived_from: M3228 failed C1 BC warm-start full run, M3228 checkpoint and summary artifact
- blocked_by: C1 remains open because M3228 failed the preregistered validation action-MSE gate
- supersedes: unlocalized interpretation of the M3228 BC gate failure
- invalidates: marking C1 complete from M3228 quick smoke alone, starting C2 guarded RL before the failed C1 warm-start path is redesigned or accepted by a new preregistration

## Success Criteria

- experiments/feasibility_audit/c5prime_c1_failure_localization.json exists with protocol c5prime_c1_failure_localization
- the diagnostic reports diagnosis_flags including the M3228 failure mode
- the diagnostic decision keeps C1 open
- the result document separates measured artifacts from inferred interpretation

## Failure Criteria

- M3229 trains a new model or changes M3228 criteria
- M3229 cannot load the M3228 checkpoint or frozen preregistration
- M3229 omits role or prefix/tail decomposition
- M3229 starts C2 or claims C1 success

## Evidence Gates

- M3229 must not train a new model or change M3228 criteria
- M3229 must reload the failed M3228 checkpoint and frozen C1 preregistration
- M3229 must decompose validation error by at least role and prefix/tail segment
- M3229 must leave C1 open if M3228 failed its preregistered gate

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not rerun C1 training
- do not relax the M3228 action-MSE gate
- do not replace the failed M3228 summary
- do not start PPO or C2 from this diagnostic
- do not claim driver performance, validation ranking, promotion, or self-ID

## Failure Taxonomy

- none

## Scoreboard

- milestone: m3229-c1-bc-warmstart-failure-localization
- type: infrastructure
- checkpoint: experiments/feasibility_audit/c5prime_c1_failure_localization.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: manual_review
- reason: no structured gates defined

## Next Blocker

C1 remains open; the next C1 attempt needs a revised preregistered warm-start design that addresses the M3229 localization.
