# Gate Utility Matrix

This document is the M1185 gate utility matrix for the paper route. It uses
existing repository artifacts only. It does not run candidate replay, train,
run PPO, use private holdout, promote a checkpoint, demote a gate, delete a
gate, or change actor inputs.

Detailed local artifacts:

```text
runs/m1185_gate_utility_matrix/summary.json
runs/m1185_gate_utility_matrix/candidate_manifest.csv
runs/m1185_gate_utility_matrix/gate_utility_matrix.csv
runs/m1185_gate_utility_matrix/gate_stack_decisions.csv
```

## Candidate Inventory

The first matrix contains twelve rows:

| Class | Count | Examples |
| --- | ---: | --- |
| Good promoted/admitted | 4 | M1154 alpha 0.05, M1123 alpha 0.15, M1156 diagnostic, M1049 short base |
| Known bad | 4 | M1069 medium PPO, M1147 actor update, M1161 refresh, M1177 relocation |
| Near miss | 2 | M1110 exact-improving actor update, M1118 failed-history repair candidate |
| Null/no-op | 2 | M1183 metadata smoke, M1184 design document |

All selected candidate artifacts have explicit path status. Non-checkpoint
artifacts are not treated as driver pass/fail rows; they are `not_applicable`
for replay and promotion gates.

## Stack A: Minimal Engineering

Stack A contains actor-contract, fresh/OOD, behavior, and basic
success/collision/clearance checks.

Result:

```text
known_bad_caught_count: 0
known_bad_missed_count: 2
good_false_reject_count: 0
recommended_use: engineering_behavior_admission_only
```

Interpretation: Stack A is necessary but not sufficient. M1069 and M1112 show
that broad fresh/OOD and behavior gates can pass while wrong-history proof
surfaces wash out. Stack A should remain core for engineering behavior, but it
cannot support self-identification or proof-retention claims by itself.

## Stack B: Balanced Public

Stack B adds compact current proof, source-diverse surface-quality, active
row15/row16 or successor terminal-margin checks, and source-rich metadata
sanity to Stack A.

Result:

```text
known_bad_caught_count: 5
known_bad_missed_count: 0
good_false_reject_count: 0
near_miss_resolution_count: 2
recommended_use: current_public_base_and_paper_route_default
```

Interpretation: Stack B should be the default active public route for the next
paper-oriented work. It catches the known proof-washout candidates and the
duplicate-dominated surface failures while avoiding the full historical stack
as a permanent blocker.

## Stack C: Full Historical Diagnostic

Stack C keeps old public replay surfaces, M1061 family-intersection, M297/M270
exact preference checks, legacy protected keys, row-specific terminal-margin
diagnostics, and other historical proof tools.

Result:

```text
known_bad_caught_count: 3
known_bad_missed_count: 0
good_false_reject_count: 0
near_miss_resolution_count: 2
recommended_use: extended_regression_and_appendix_diagnostics
```

Interpretation: Stack C contains real value. It caught M1069, M1112, and M1149
proof-washout failures. But it is also lineage-specific and partially
redundant with Stack B. It should remain available for promotion, branch
synthesis, and paper appendix diagnostics, not automatically veto every
engineering baseline or finite-window comparison.

## Provisional Gate Classes

| Class | Gates |
| --- | --- |
| Core | actor contract, fresh/OOD behavior, basic success/collision/clearance, source-diverse surface quality, source-rich metadata sanity, private holdout isolation |
| Research-only | current balanced public proof subset, M297/M270 exact preference |
| Extended-regression | row15/row16 terminal-margin surfaces, old public replay surfaces, M1061 family-intersection |
| Legacy | old 9944 protected singleton |
| Deprecated | sign-wrong or metric-artifact objectives |

These are recommendations only. M1185 does not demote, delete, or rewrite
gates.

## Key Findings

1. Stack A is core but insufficient for proof. It can miss proof washout that
   preserves aggregate behavior.
2. Stack B is the best default active gate stack for near-term paper-route
   work because it catches both wrong-history washout and surface-quality
   failures.
3. Stack C should become extended regression and appendix diagnostics unless a
   later executable audit shows one of its members catches a unique failure
   that Stack B misses.
4. Old singletons such as `9944|perturbed|28|28` should remain legacy
   diagnostics, not single-row global blockers.
5. Deprecated objective directions should not guide future training or
   promotion unless a new manifest justifies reinstatement.

## Next Route

The matrix is sufficient for a policy-design milestone:

```text
m1186-paper-route-active-gate-policy-design
```

M1186 should turn this matrix into an active gate policy. It should still avoid
deleting historical tooling. The expected output is a written policy separating
daily engineering gates, active public proof gates, extended regression gates,
and legacy diagnostics.
