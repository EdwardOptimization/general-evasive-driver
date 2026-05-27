# m1052-v4-public-base-guarded-ppo-short-escalation-promotion-audit Research Review

## Summary

- Generated at UTC: 20260527T040451Z
- Type: gate
- Gate tier: promotion
- Promotion decision: guarded_ppo_short_escalation_promote_public_gate_base
- Decision reason: M1052 promotes seed61049 4096-step guarded PPO checkpoint as current public-gate base after three short-PPO public-gate passes; scope remains public-gate only

## Hypothesis

One of the three 4096-step guarded PPO candidates can be selected as the next public-gate base using explicit public-gate, row15/row16, and exact-retention evidence.

## Lineage

- parent_checkpoint: runs/ppo_m1044_combined_active_set_guarded_smoke_seed61044/checkpoint.pt, runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt, runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt, runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt
- parent_dataset: docs/m1051-v4-public-base-guarded-ppo-short-escalation-synthesis.md, runs/m1050_guarded_ppo_short_escalation_repeat_summary.json
- parent_config: experiments/manifests/m1051-v4-public-base-guarded-ppo-short-escalation-synthesis.json
- parent_objective: audit whether a 4096-step guarded PPO raw candidate should become the next public-gate base
- derived_from: m1051-v4-public-base-guarded-ppo-short-escalation-synthesis
- blocked_by: M1049/M1050 produced three short-PPO candidates but none has been separately audited for public-base promotion
- supersedes: None
- invalidates: promoting a 4096-step candidate directly from the run milestone without a promotion audit

## Success Criteria

- promotion audit artifact exists
- candidate set is explicit
- selection criteria are explicit
- selected checkpoint or rejection is explicit
- scope limits are explicit
- no training or PPO occurs
- private holdout is not used

## Failure Criteria

- promotion audit artifact is missing
- candidate selection is ambiguous
- training or PPO starts
- private holdout is used
- promotion scope exceeds public-gate evidence

## Evidence Gates

- M1052 must not train
- M1052 must not run PPO
- M1052 must not use private holdout
- M1052 must select or reject among the three 4096-step raw candidates using explicit public-gate evidence
- M1052 must keep promotion scope public-gate only
- M1052 must require exact/proof/source-diverse/fresh/OOD/behavior evidence and row15/row16 retention

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not change actor inputs
- do not claim medium or long PPO stability
- do not claim paper-level generalization
- do not select solely by aggregate return

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1052-v4-public-base-guarded-ppo-short-escalation-promotion-audit
- type: driver_candidate
- checkpoint: runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: guarded_ppo_short_escalation_promote_public_gate_base
- reason: M1052 promotes seed61049 4096-step guarded PPO checkpoint as current public-gate base after three short-PPO public-gate passes; scope remains public-gate only

## Next Blocker

m1053-v4-public-base-guarded-ppo-short-promotion-synthesis
