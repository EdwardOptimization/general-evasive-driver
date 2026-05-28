# m1262-paper-route-richer-fault-regret-boundary-retarget-implementation Research Review

## Summary

- Generated at UTC: 20260528T115718Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: not_applicable
- Decision reason: M1262 passes as infrastructure if it implements focused retargeting, reports strict accepted rows and anti-collision diagnostics, and preserves all no-training/no-threshold-relaxation guardrails.

## Hypothesis

A bounded obstacle-geometry retarget around M1259 pair 5 can increase two-sided cross-regret while keeping own-branch best actions viable.

## Lineage

- parent_checkpoint: runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt
- parent_dataset: docs/m1261-paper-route-richer-fault-regret-boundary-retarget-design.md, docs/m1260-paper-route-richer-fault-capability-source-result-audit.md, runs/m1259_richer_fault_capability_source_smoke/matched_capability_pairs.csv, runs/m1259_richer_fault_capability_source_smoke/trajectory_proposals.csv
- parent_config: experiments/manifests/m1261-paper-route-richer-fault-regret-boundary-retarget-design.json, configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json
- parent_objective: implement and smoke-test bounded regret-boundary retargeting around M1259 pair 5
- derived_from: m1261-paper-route-richer-fault-regret-boundary-retarget-design
- blocked_by: M1261 admits a bounded implementation smoke
- supersedes: another unstructured richer-fault source run
- invalidates: None

## Success Criteria

- src/autodrift/capability_separable_regret_retarget.py exists
- tests/test_capability_separable_regret_retarget.py exists
- runs/m1262_richer_fault_regret_boundary_retarget_smoke/summary.json exists
- accepted_regret_retarget_rows.csv exists
- strict accepted row count is reported
- own_branch_viability_fail_count is reported
- all_four_rollouts_collision_count is reported
- actor_parameters_changed == false
- training_started == false
- ppo_used == false
- promoted == false
- labels_enter_actor_input == false
- private holdout remains unused
- no actor-input contract expansion occurs

## Failure Criteria

- tool or tests are missing
- source reconstruction is unreliable but run continues anyway
- accepted thresholds are lowered
- negative own-branch margins are accepted
- training or PPO starts
- promotion occurs
- current single-track proxy faults are claimed as true physical per-wheel faults

## Evidence Gates

- M1262 must preserve actor input contract
- M1262 must not train controllers
- M1262 must not run PPO
- M1262 must not use private holdout
- M1262 must not promote
- M1262 must preserve strict accepted-source criteria
- M1262 must report anti-collision-dominance diagnostics

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not promote
- do not add hidden parameters, fault labels, oracle outcomes, or search outputs to actor inputs
- do not lower min_cross_regret_margin
- do not accept negative own-branch margins
- do not treat asymmetric_success_drop as strict accepted source-positive
- do not claim current single-track proxies are true single-wheel or per-wheel faults

## Failure Taxonomy

- none

## Scoreboard

- No scoreboard row recorded.

## Next Blocker

m1262-paper-route-richer-fault-regret-boundary-retarget-implementation
