# M1223 Paper-Route Current-Family Boundary Source Negative Audit

## Summary

M1223 audits the M1222 normal-success boundary source result before launching
another narrow run.

Decision:

```text
boundary_source_negative_audit_route_to_causal_history_synthesis
```

No new source mining, outcome intervention, training, PPO, checkpoint repair,
promotion, private holdout, profile tuning, or actor-input change occurs in
M1223.

## Evidence Reviewed

Primary artifacts:

```text
runs/m1222_current_family_normal_success_boundary_source_smoke/summary.json
runs/m1222_current_family_normal_success_boundary_source_smoke/normal_window_rows.csv
runs/m1222_current_family_normal_success_boundary_source_smoke/candidate_scores.csv
docs/m1222-paper-route-current-family-normal-success-boundary-source-smoke.md
```

M1222 result:

```text
snapshot_count:             512
candidate_pairs:           2400
candidate_rows:            7200
accepted_rows:                0
corpus_passed:             false
actor_checksum_changed:    false
ppo_used:                  false
```

## Failure Classification

M1222 is not:

```text
no_near_boundary_normal_success_windows
```

because it found:

```text
near_boundary_preferred_snapshots: 45
near_boundary seeds:              36
near_boundary targets:             3
```

M1222 is not:

```text
near_boundary_exists_but_no_action_gap
```

because it found:

```text
wrong_first_action_l2 >= 0.002 rows:              6927
wrong_action_sequence_mean_l2 >= 0.006 rows:       707
preferred/rejected action mean_l2 >= 0.010 rows:   274
all action threshold rows:                         274
```

M1222 is:

```text
near_boundary_action_gap_but_no_outcome_gap
```

because:

```text
margin_gap >= 0.010 rows: 0
success_drop_rows:        0
candidate_normal_success_rate: 1.000
candidate_wrong_success_rate:  1.000
max margin_gap:           0.002370
mean margin_gap:         -0.000115
```

## What The Negative Result Means

The current-family actor is not hidden-path dead:

```text
M1220 reset/random/scaled hidden perturbations moved action.
```

The current-family source route is not action-dead:

```text
M1222 produced 274 all-action-threshold rows.
```

The blocker is outcome materialization:

```text
The wrong-history action differences are not yet placed on terminal-margin or
success-sensitive scene boundaries.
```

So training from M1222 would be wrong. The accepted corpus is empty, and the
action-divergent rows are not yet proof rows.

## Route Options

### Option A: Terminal-Boundary Relocation

Use M1222 action-divergent rows as candidate source rows, then relocate obstacle
timing/geometry toward target terminal margins.

Pros:

- directly addresses the observed failure mode;
- M1222 candidate rows include explicit obstacle x/y geometry, unlike older
  M1175 artifact-only rows;
- keeps the current-family actor and config.

Risks:

- M1177 showed relocation can collapse onto a small active set;
- the current pipeline may need an adapter from M1222 `candidate_scores.csv` to
  relocation-compatible candidate rows;
- relocation is still not self-ID proof until source-diverse accepted rows pass.

### Option B: Longer-Horizon Outcome Scoring

Re-score M1222 candidates with longer continuation horizon and terminal-margin
metrics.

Pros:

- smaller engineering change;
- directly tests whether a 12-step horizon missed delayed outcome effects.

Risks:

- M1222 max margin gap is only `0.002370`, far below the `0.010` gate;
- both normal and wrong branches succeeded at rate `1.000`;
- longer horizon alone may only confirm outcome-insensitivity.

### Option C: Stronger Cross-Family / Fault Source

Move to explicit dynamics variation such as capability-step/fault/extreme
hidden-condition source mining.

Pros:

- matches the long-term objective of robust evasive driving under extreme
  dynamics changes;
- likely creates larger real-history differences than same-family public seeds.

Risks:

- changes the source distribution before closing the current-family causal
  history branch;
- must avoid turning fault labels into actor inputs or oracle answers;
- should be governed by a new branch and source-holdout discipline.

### Option D: Immediate Training / PPO

Rejected.

Reason:

```text
No accepted source rows exist, and action divergence without outcome
degradation is not sufficient supervision or proof.
```

## Audit Decision

Do not continue with another narrow run immediately.

The current causal-history branch has accumulated enough evidence to synthesize:

```text
M1215: causal-history gate design
M1217: current-family matched-current source exists
M1218: wrong/delayed action screen negative
M1220: hidden path exists but natural histories are action-equivalent
M1222: broader source finds action gaps but no outcome gaps
```

The next step should be branch synthesis. It should decide whether to:

```text
1. open a terminal-boundary materialization branch;
2. open a stronger cross-family/fault source branch;
3. run a bounded longer-horizon check first;
4. stop current-family causal-history source mining.
```

## Supported Claims

Supported:

```text
Current-family L3 actors have a functional hidden path.
The original M1217 matched-current source is not action-critical.
A broader normal-success source can produce action-divergent wrong histories.
Those action-divergent histories do not currently produce margin or success
degradation.
```

## Blocked Claims

Blocked:

```text
history necessity;
recurrent belief;
online self-identification;
closed-loop causal-history outcome proof;
training readiness from current M1222 rows;
paper-level claim that GRU uses command-response history.
```

## Decision

```text
boundary_source_negative_audit_route_to_causal_history_synthesis
```

Next blocker:

```text
m1224-paper-route-causal-history-evidence-synthesis
```
