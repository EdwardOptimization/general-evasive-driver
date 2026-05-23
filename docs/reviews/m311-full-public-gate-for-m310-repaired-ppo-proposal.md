# m311-full-public-gate-for-m310-repaired-ppo-proposal Research Review

## Summary

- Generated at UTC: 20260523T051430Z
- Type: driver_candidate
- Gate tier: promotion
- Promotion decision: reject_m310_repaired_protected_key_window_failure
- Decision reason: Six replay gates pass but protected key 9944 fails for M310 repaired while M307 and reference pass so promotion is rejected before behavior gates

## Hypothesis

The M310 exact-repaired PPO proposal can pass the full public gate stack and become the next public-gate base.

## Lineage

- parent_checkpoint: runs/m306_exact_repair_from_raw_s40_seed10091/candidate_checkpoint.pt, runs/m310_exact_repair_from_raw_s40_seed10095/candidate_checkpoint.pt
- parent_dataset: runs/m183_m168_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv, runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv, runs/m193_m189_boundary_outcome_corpus_seed9630/boundary_outcome_corpus.csv, runs/m212_m204_boundary_outcome_corpus_seed10040/boundary_outcome_corpus.csv, runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.csv, runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv, runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz
- parent_config: configs/ppo_m310_exact_repaired_proposal_smoke.json, experiments/manifests/m310-fresh-ppo-proposal-exact-repair-smoke.json, docs/m310-fresh-ppo-proposal-exact-repair-smoke.md
- parent_objective: run full public promotion gate for M310 exact-repaired PPO proposal
- derived_from: m310-fresh-ppo-proposal-exact-repair-smoke
- blocked_by: m310-fresh-ppo-proposal-exact-repair-smoke
- supersedes: None
- invalidates: None

## Success Criteria

- candidate passes all six public replay gates versus M307
- candidate passes protected-key diagnostic
- candidate retains behavior on seeds 9505 and 9506
- candidate keeps exact M297 and exact M270 improvements versus M307
- actor input contract remains unchanged

## Failure Criteria

- any replay gate fails
- protected key fails
- behavior seeds materially regress
- exact M297 or exact M270 regresses
- actor observation inputs change

## Evidence Gates

- candidate exact M297 and exact M270 remain non-regressing versus M307
- M183/M168 replay gate versus M307
- M183/M170 replay gate versus M307
- M193/M189 replay gate versus M307
- M212/M204 replay gate versus M307
- M223/M219 replay gate versus M307
- M267/M264 replay gate versus M307
- protected key 9944 guard
- behavior seeds 9505 and 9506
- research validator

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not promote on first replay gates alone
- do not loosen protected-key or behavior gates
- do not change actor inputs
- do not ignore exact M297 or exact M270 regression

## Failure Taxonomy

- protected_key_window_failure
- promotion_gate_failure

## Scoreboard

- milestone: m311-full-public-gate-for-m310-repaired-ppo-proposal
- type: driver_candidate
- checkpoint: runs/m310_exact_repair_from_raw_s40_seed10095/candidate_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: reject_m310_repaired_protected_key_window_failure
- reason: Six replay gates pass but protected key 9944 fails for M310 repaired while M307 and reference pass so promotion is rejected before behavior gates

## Next Blocker

m312-m310-protected-key-window-failure-audit
