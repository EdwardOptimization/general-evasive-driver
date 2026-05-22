# m230-m229-protected-key-failure-audit Research Review

## Summary

- Generated at UTC: 20260522T130434Z
- Type: gate
- Gate tier: process
- Promotion decision: repair_with_protected_key_snippet_surface
- Decision reason: M230 finds M229 restored replay retention but failed protected key because 9944 is outside the M223 snippet anchor surface; nearest M223 geometry distance is 0.571770 and snippet anchor loss was near zero so export protected-key snippets before more PPO

## Hypothesis

M229 proves snippet action anchoring restores replay-surface retention but not the historical protected key. The remaining failure is likely a protected-key coverage/window issue rather than old replay washout.

## Lineage

- parent_checkpoint: runs/m224_m219_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10063/optimized_checkpoint.pt, runs/ppo_m226_guarded_from_m224_seed5218/checkpoint.pt, runs/ppo_m229_snippet_anchor_from_m224_seed5219/checkpoint.pt
- parent_dataset: runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.npz, runs/m229_critical_key_seed9944/protected_cases.csv, runs/m229_critical_key_seed9944/guard_results.csv
- parent_config: configs/ppo_m229_snippet_anchor_from_m224_smoke.json
- parent_objective: rollout-state M224 baseline action anchor, preferred-only M224 boundary snippet action anchor
- derived_from: m229-snippet-anchored-ppo-smoke-from-m224
- blocked_by: m229-snippet-anchored-ppo-smoke-from-m224
- supersedes: None
- invalidates: None

## Success Criteria

- classify whether M229's protected-key failure is normal-margin-window only or margin-gap collapse
- compare M224/M226/M229 protected key candidates
- check whether the protected key is represented by the M223 snippet anchor surface
- pre-register exactly one next repair path before any more PPO
- keep M224 current best unless all protected-key gates pass

## Failure Criteria

- run another PPO seed before the audit
- promote M229 because fixed loss and replay gates passed
- ignore the protected key failure
- relax protected-key thresholds after observing M229

## Evidence Gates

- M229 protected key guard
- M229 replay gates
- M229 train_metrics snippet_action_anchor_loss_mean
- M223 snippet corpus coverage against protected key

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not repeat or lengthen M229 before the audit
- do not loosen the protected-key normal-margin window after seeing M229
- do not lower clearance just to satisfy one historical key
- do not change actor inputs

## Failure Taxonomy

- protected_key_window_failure
- promotion_gate_failure

## Scoreboard

- milestone: m230-m229-protected-key-failure-audit
- type: gate
- checkpoint: runs/m224_m219_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10063/optimized_checkpoint.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.844231
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: repair_with_protected_key_snippet_surface
- reason: M230 finds M229 restored replay retention but failed protected key because 9944 is outside the M223 snippet anchor surface; nearest M223 geometry distance is 0.571770 and snippet anchor loss was near zero so export protected-key snippets before more PPO

## Next Blocker

Export protected-key snippets or a small protected-key family before any more PPO.
