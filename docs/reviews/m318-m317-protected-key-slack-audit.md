# m318-m317-protected-key-slack-audit Research Review

## Summary

- Generated at UTC: 20260523T054810Z
- Type: gate
- Gate tier: proof
- Promotion decision: admit_m319_m317_family_protected_surface_refresh
- Decision reason: M318 classifies 9944 as single-key window saturation after M317 with normal-margin slack about 4.8e-6 and admits a source-diverse protected-surface refresh before more PPO

## Hypothesis

After M317, the old 9944 protected key is so close to the normal-margin upper window that future PPO acceptance will be dominated by a single saturated row unless the protected surface is refreshed or converted to a source-diverse gate.

## Lineage

- parent_checkpoint: runs/m316_m314_to_repaired_protected_key_bounded_interpolation/checkpoints/alpha_0_0025.pt
- parent_dataset: runs/m133_zero_relvel_s60_strict_60ep_seed9900/outcome_sensitive_snippets.csv, runs/m133_zero_relvel_s60_strict_60ep_seed9920/outcome_sensitive_snippets.csv, runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv
- parent_config: experiments/manifests/m317-full-public-gate-for-m316-a0-0025.json, docs/m317-full-public-gate-for-m316-a0-0025.md
- parent_objective: audit whether the old protected key should keep acting as a single hard trust-region veto after M317 leaves only micro slack
- derived_from: m317-full-public-gate-for-m316-a0-0025
- blocked_by: m317-full-public-gate-for-m316-a0-0025
- supersedes: None
- invalidates: None

## Success Criteria

- quantify M317 slack for protected key 9944
- compare old key behavior against current-family protected or wrong-history rows if available
- produce a next decision: keep single key, refresh multi-key surface, or redesign protected-surface distribution gate
- no training is run

## Failure Criteria

- audit runs PPO or actor update
- audit recommends bypassing 9944 without replacement evidence
- audit changes actor input contract
- audit cannot identify the next protected-surface decision

## Evidence Gates

- do not run PPO
- preserve human-view actor input contract
- quantify remaining protected-key slack at M317 base
- classify whether 9944 is stale singleton or representative saturated family
- decide whether to refresh source-diverse protected surface before more PPO

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not bypass protected key without documented replacement evidence
- do not run another PPO before the slack audit
- do not change actor inputs
- do not tune from private holdouts

## Failure Taxonomy

- none

## Scoreboard

- milestone: m318-m317-protected-key-slack-audit
- type: gate
- checkpoint: runs/m316_m314_to_repaired_protected_key_bounded_interpolation/checkpoints/alpha_0_0025.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m319_m317_family_protected_surface_refresh
- reason: M318 classifies 9944 as single-key window saturation after M317 with normal-margin slack about 4.8e-6 and admits a source-diverse protected-surface refresh before more PPO

## Next Blocker

m319-m317-family-protected-surface-refresh
