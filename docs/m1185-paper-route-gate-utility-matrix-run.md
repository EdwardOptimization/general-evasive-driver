# M1185 Paper-Route Gate Utility Matrix Run

## Summary

M1185 builds the first paper-route gate utility matrix from existing artifacts.
It follows the design from:

```text
docs/m1184-paper-route-gate-utility-audit-design.md
```

No candidate replay, actor training, PPO, promotion, private holdout, gate
demotion, gate deletion, or actor-input change occurred.

## Artifacts

```text
docs/gate-utility-matrix.md
runs/m1185_gate_utility_matrix/summary.json
runs/m1185_gate_utility_matrix/candidate_manifest.csv
runs/m1185_gate_utility_matrix/gate_utility_matrix.csv
runs/m1185_gate_utility_matrix/gate_stack_decisions.csv
```

## Result

```text
result_class: gate_utility_matrix_ready
candidate_rows: 12
gate_utility_rows: 13
gate_stack_rows: 3
required_artifacts_pass: true
candidate_replay_started: false
training_started: false
ppo_used: false
private_holdout_used: false
promoted: false
actor_inputs_changed: false
```

Candidate class coverage:

```text
good promoted/admitted: 4
known bad: 4
near miss: 2
null/no-op: 2
```

## Stack Decision

Stack A is classified as core engineering infrastructure but insufficient for
proof. It protects actor contract and broad behavior but misses known proof
washout cases such as M1069 and M1112.

Stack B is the recommended active public route. It combines engineering checks
with compact current proof, source-diverse surface quality, active
terminal-margin checks, and source-rich metadata sanity. It catches the known
bad candidates in this first matrix without false-rejecting the selected good
public candidates.

Stack C remains valuable as extended regression and paper appendix diagnostics.
It caught real failures, but several members are lineage-specific and should
not automatically veto every future engineering baseline or finite-window
controller comparison.

## Gate Classification

Provisional classes:

```text
core:
  actor_contract_no_privileged_input
  fresh_ood_behavior_retention
  minimal_success_collision_clearance
  source_diverse_surface_quality_gate
  source_rich_metadata_sanity
  private_holdout_isolation

research-only:
  current_balanced_public_proof_subset
  m297_m270_exact_preference

extended-regression:
  row15_row16_terminal_margin_surfaces
  old_public_replay_surfaces
  m1061_family_intersection

legacy:
  old_9944_protected_singleton

deprecated:
  sign_wrong_or_metric_artifact_objectives
```

This is not an active demotion. A later policy milestone must decide how the
classification changes daily gates, promotion gates, and extended regression.

## Evidence Notes

- M1069 shows Stack A can pass while proof replay, family-intersection, and
  source-diverse gates fail.
- M1112 shows exact objective and behavior can pass while wrong-history proof
  surfaces wash out.
- M1149 shows row15-promoted actor update can keep normal success while making
  wrong-history branches safe.
- M1161 and M1177 show source budget can look broad while materialized proof
  surfaces remain duplicate-dominated.
- M1156 and M1158 show the current public base passes the expanded public
  diagnostics, but its near-zero wrong-history margin caveat must remain
  visible.
- M1183 is infrastructure-only metadata readiness and must be `not_applicable`
  for driver checkpoint gates.

## Decision

```text
gate_utility_matrix_pass_route_to_active_gate_policy_design
```

The next milestone should be:

```text
m1186-paper-route-active-gate-policy-design
```

M1186 should convert this matrix into a written active gate policy without
deleting historical tools or claiming driver-performance progress.
