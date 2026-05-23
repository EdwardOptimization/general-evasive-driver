# m312-m310-protected-key-window-failure-audit Research Review

## Summary

- Generated at UTC: 20260523T051831Z
- Type: gate
- Gate tier: proof
- Promotion decision: admit_m313_protected_key_bounded_interpolation_probe
- Decision reason: M312 classifies M310 failure as protected-key normal-margin window violation not broad proof washout and preserves M307 as base

## Hypothesis

M310 failed the protected key because exact repair shifted the protected-key margin outside the accepted window even though broad replay proof surfaces remained intact.

## Lineage

- parent_checkpoint: runs/m306_exact_repair_from_raw_s40_seed10091/candidate_checkpoint.pt, runs/m310_exact_repair_from_raw_s40_seed10095/candidate_checkpoint.pt
- parent_dataset: runs/m133_zero_relvel_s60_strict_60ep_seed9900/outcome_sensitive_snippets.csv, runs/m133_zero_relvel_s60_strict_60ep_seed9920/outcome_sensitive_snippets.csv, runs/m311_full_public_gate_for_m310_repaired/full_gates/critical_key_seed9944/guard_results.csv
- parent_config: experiments/manifests/m311-full-public-gate-for-m310-repaired-ppo-proposal.json, docs/m311-full-public-gate-for-m310-repaired-ppo-proposal.md
- parent_objective: audit why exact-repaired PPO candidate passes replay surfaces but fails protected key window
- derived_from: m311-full-public-gate-for-m310-repaired-ppo-proposal
- blocked_by: m311-full-public-gate-for-m310-repaired-ppo-proposal
- supersedes: None
- invalidates: None

## Success Criteria

- classify the M311 protected-key failure mechanism
- identify whether the failure is singleton window saturation or a missing objective term
- register the next repair or refresh milestone
- preserve M307 as the public-gate base

## Failure Criteria

- audit cannot reproduce or interpret the protected-key failure
- audit proposes promotion despite protected-key failure
- audit requires actor input changes

## Evidence Gates

- inspect protected key 9944 guard results
- compare M307 M310 and known-failing M239 margins
- classify stale singleton versus systematic protected-surface shift
- decide whether next repair needs protected-key term or protected-surface refresh
- do not promote M310

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not bypass the protected-key failure
- do not promote M310 from replay gates alone
- do not change actor inputs
- do not run new PPO before the protected-key failure is classified

## Failure Taxonomy

- none

## Scoreboard

- milestone: m312-m310-protected-key-window-failure-audit
- type: gate
- checkpoint: runs/m306_exact_repair_from_raw_s40_seed10091/candidate_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m313_protected_key_bounded_interpolation_probe
- reason: M312 classifies M310 failure as protected-key normal-margin window violation not broad proof washout and preserves M307 as base

## Next Blocker

m313-m310-protected-key-bounded-interpolation-probe
