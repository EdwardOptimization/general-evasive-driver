# m385-old-key-recovery-residual-repair-probe Research Review

## Summary

- Generated at UTC: 20260523T134953Z
- Type: gate
- Gate tier: proof
- Promotion decision: admit_m386_full_public_gate_for_m385_micro_a00075
- Decision reason: M385 rejects direct recovery-repair endpoint and regular alphas by proof washout; micro alpha 0.00075 passes exact cumulative old-key source-diverse and first replay gates while alpha 0.001 first fails M267/M264

## Hypothesis

Exact repair using the replay-selected M384 old-key recovery residual can move beyond the M378 alpha 0.05 base toward the alpha 0.1 direction while improving gap-tail normal margins and preserving M297/M270 proof objectives.

## Lineage

- parent_checkpoint: runs/m378_v2_gap_tail_final_interpolation/checkpoints/alpha_0_05.pt, runs/m378_v2_gap_tail_final_interpolation/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m384_old_key_local_recovery_targets/old_key_recovery_corpus.npz, runs/m377_cumulative_gap_tail_v2_old_key_preference_corpus/old_key_preference_corpus.npz, runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz
- parent_config: experiments/manifests/m384-old-key-local-recovery-target-export.json
- parent_objective: probe exact repair with replay-selected old-key recovery residual before any PPO continuation
- derived_from: m384-old-key-local-recovery-target-export
- blocked_by: m384-old-key-local-recovery-target-export
- supersedes: None
- invalidates: None

## Success Criteria

- run exact repair with M384 old-key recovery corpus and no PPO
- candidate or bounded interpolation passes exact M297/M270 no-regression
- cumulative old-key replay gap-tail gate improves or no longer fails for the M380 rows
- if cumulative old-key passes then source-diverse protected and first replay gates are admitted
- all artifacts and failure classifications are documented
- research validation passes

## Failure Criteria

- exact repair regresses M297 or M270
- recovery residual improves but closed-loop cumulative old-key replay still fails
- wrong-history branch is made safe by the repair
- actor contract is changed
- research validation fails

## Evidence Gates

- no PPO run
- exact M297 no-regression
- exact M270 no-regression
- old-key recovery residual decreases or remains bounded
- cumulative old-key replay gate before source-diverse or first replay gates
- preserve actor input contract

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote a checkpoint directly
- do not lower old-key thresholds
- do not add hidden or oracle actor inputs
- do not replace direct steer/throttle/brake output
- do not accept exact loss improvement without closed-loop replay

## Failure Taxonomy

- proof_washout
- protected_key_window_failure

## Scoreboard

- milestone: m385-old-key-recovery-residual-repair-probe
- type: gate
- checkpoint: runs/m385_recovery_repair_micro_interpolation/checkpoints/alpha_0_00075.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m386_full_public_gate_for_m385_micro_a00075
- reason: M385 rejects direct recovery-repair endpoint and regular alphas by proof washout; micro alpha 0.00075 passes exact cumulative old-key source-diverse and first replay gates while alpha 0.001 first fails M267/M264

## Next Blocker

m386-full-public-gate-for-m385-a00075
