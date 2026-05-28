# M1184 Paper-Route Gate Utility Audit Design

## Summary

M1184 designs the gate utility audit required by the paper-route plan before
historical proof rows, repair tools, and replay gates remain active blockers or
are demoted. This milestone is design-only. It does not run candidate replay,
change gates, train an actor, run PPO, use private holdout, promote a
checkpoint, or change actor inputs.

The follow-up milestone is pre-registered as:

```text
experiments/manifests/m1185-paper-route-gate-utility-matrix-run.json
```

## Decision

```text
paper_route_gate_utility_audit_design_admit_matrix_run
```

The audit should convert the historical gate stack into an evidence-governed
classification:

```text
core
research-only
extended-regression
legacy
deprecated
```

No classification takes effect in M1184. M1185 may produce the matrix and
recommendations from existing artifacts only. Any actual gate demotion,
deletion, or promotion requires a later milestone after the matrix exists.

## Why This Audit Is Needed

M1182a changed the paper route. The project should not assume that every
historical row-specific gate is a permanent engineering blocker, and it should
also not delete old proof gates just because they are inconvenient. The current
risk is two-sided:

- keeping every historical row active can over-constrain future finite-window,
  GRU, source-rich, or PPO comparisons around lineage-specific proof rows;
- demoting old gates without evidence can erase real failure detectors that
  previously caught proof washout, wrong-history collapse, or actor-contract
  regressions.

The audit therefore asks a concrete question:

```text
Which gates catch real candidate failures, which gates are redundant or
lineage-specific diagnostics, and which gates are unsafe to use as future
training blockers?
```

## Guardrails

M1184 and M1185 must preserve these boundaries:

- no actor-input change;
- no hidden or oracle deployable signals;
- no candidate replay in M1184;
- no actor training or PPO;
- no checkpoint promotion;
- no private holdout;
- no gate demotion or deletion;
- no paper-level driver-performance or self-identification claim.

M1185 may inspect existing manifests, docs, scoreboard rows, and already
written run summaries. If a needed candidate artifact is missing, M1185 should
return `candidate_inventory_insufficient` and route to a candidate inventory
milestone rather than weakening the audit.

## Candidate Classes

M1185 should populate a candidate manifest with at least four classes.

### Good Promoted Or Admitted Candidates

These candidates should be accepted by any active gate stack that claims to be
usable for the current paper route. They are used to measure false rejects.

Initial inventory targets:

- M399 alpha `0.05` older public proof-hardening point;
- M1044 / M1049 / M1050 short-PPO or repair lineage checkpoints that were
  admitted by their local public gates;
- M1123 alpha `0.15`, the previous row15 projection public-gate base;
- M1154 alpha `0.05`, the current public-gate base;
- no-op current-base candidate, exactly equal to M1154 alpha `0.05`.

M1185 should resolve exact paths from `experiments/scoreboard.csv`,
`docs/current-status.md`, and milestone docs. If a path is unavailable, record
the candidate as `path_missing` instead of inventing a path.

### Known Bad Candidates

These candidates should be caught by useful gates. They measure false accepts.

Initial inventory targets:

- M1069 medium-PPO family, classified historically as proof washout;
- M1147 actor-coupling or repair candidate that made wrong-history branches too
  safe;
- M1110-style actor update that lost wrong-history proof retention;
- M1161 / M1177 duplicate-dominated surface-derived routes, where source
  diversity collapsed;
- old sign-wrong or low-tail actor candidates that improved a scalar metric but
  violated the intended proof direction;
- any candidate already documented as `objective_overfit`, `metric_artifact`,
  `proof_washout`, or `scenario_sampling_failure`.

M1185 should not rerun replay to prove these are bad. It should use existing
documents and summaries to label their historical failure mode.

### Near-Miss Candidates

These candidates are useful because different gate stacks may legitimately
disagree. They help decide which gates are core versus extended regression.

Initial inventory targets:

- interpolation alphas just above a historically safe boundary;
- candidates that passed exact objective gates but failed a closed-loop replay
  gate;
- candidates that repaired normal-history safety while making wrong-history
  rollouts safe;
- candidates with behavior retention but reduced mechanism proof;
- candidates with current-base or source-rich metadata readiness but no proof
  conversion.

### Null Or No-Op Candidates

These catch gate and matrix bugs.

Initial inventory targets:

- exact current public-gate base as identity candidate;
- documentation-only milestones with no checkpoint;
- source-rich metadata smoke artifact that is not a checkpoint;
- unavailable-path sentinel rows.

The expected behavior is that checkpoint gates should mark non-checkpoint rows
as `not_applicable`, not pass them as drivers or fail the whole audit.

## Gate Stacks

M1185 should compare three gate stacks. The stacks are classification tools,
not new promotion rules.

### Stack A: Minimal Engineering Gate

Purpose: identify the lowest-friction gate stack that protects deployable
driver behavior without binding the paper route to row-specific proof history.

Required checks:

- actor-contract and no-privileged-input status;
- no actor-backbone or deployable-input change unless explicitly declared;
- behavior seeds and basic success/collision/clearance retention where
  existing artifacts are available;
- fresh or OOD scenario summaries when already available;
- no private-holdout contamination;
- no training/PPO/promotion shortcut mismatch.

Expected use:

- engineering cleanup;
- baseline L0/L1/L2/L3 comparison readiness;
- broad scenario evaluation admission.

Stack A should not be used as self-identification proof by itself.

### Stack B: Balanced Public Gate

Purpose: protect the active public proof base while avoiding permanent
dependence on every historical row.

Required checks:

- all Stack A checks;
- compact source-diverse proof subset, if available;
- current active rollback/protected subset such as row15/row16 or successor
  equivalents;
- one current-family wrong-history or action-divergence proof surface;
- source-rich metadata sanity after M1183;
- exact objective non-regression only for active proof objectives, not every
  historical objective.

Expected use:

- public-base hardening;
- guarded PPO admission;
- candidate acceptance before private holdout or paper-scale evaluation.

### Stack C: Full Historical Diagnostic Gate

Purpose: retain deep regression coverage and explain historical compatibility,
not necessarily veto every future paper-route candidate.

Candidate members:

- old public replay surfaces such as M183/M170 and related M183/M193 rows;
- protected key and protected-surface diagnostics;
- M267/M264 current-family wrong-history rows;
- M297/M270 rejected-history preference/exact objective checks;
- M1061 family-intersection diagnostics;
- row15/row16 materialized and promoted surfaces;
- terminal-margin cliff diagnostics;
- source-diverse and legacy repair/projection checks.

Expected use:

- extended regression;
- paper appendix diagnostics;
- compatibility audits;
- failure localization.

Stack C may still contain core gates, but M1185 should not assume every member
is core. It should measure or document unique failure coverage versus cost and
false rejects.

## Gate Utility Metrics

For each candidate class and gate stack, M1185 should record:

```text
known_bad_caught_count
known_bad_missed_count
good_false_reject_count
near_miss_resolution_count
not_applicable_count
runtime_seconds_or_estimate
artifact_count
lineage_specificity
overlap_with_other_gates
private_holdout_contamination_risk
recommended_classification
classification_reason
```

Recommended categorical fields:

```text
candidate_class
candidate_lineage
historical_failure_type
gate_name
gate_stack
gate_tier
gate_result
evidence_source
path_status
```

## Classification Rules

M1185 should assign each gate or corpus one of the following provisional
classes. These are recommendations only until a later gate-cleanup milestone.

### Core

Use when the gate:

- catches known bad candidates or protects actor-contract integrity;
- has low false rejection on good promoted/admitted candidates;
- is not strongly tied to one obsolete checkpoint family;
- is cheap enough or important enough to run frequently;
- protects a claim needed for engineering admission or paper-scale comparison.

### Research-Only

Use when the gate:

- is necessary to support a self-identification, history-necessity, or
  mechanism claim;
- is not required for generic driver performance admission;
- should be reported in a paper or appendix but should not automatically block
  all engineering cleanup.

### Extended-Regression

Use when the gate:

- catches real failures but is expensive, redundant, or too lineage-specific
  for every milestone;
- should run before promotion, synthesis, or major branch changes;
- should remain available for compatibility audits.

### Legacy

Use when the gate:

- records a historical diagnostic or old proof row;
- no longer catches unique known bad candidates in the candidate matrix;
- may still help explain older milestone decisions;
- should not be deleted yet.

### Deprecated

Use when the gate:

- encodes a sign-wrong objective, metric artifact, exhausted active set, or
  obsolete row-specific blocker;
- creates false confidence or repeatedly pushes the branch toward local
  gate-passing rather than broader evidence;
- should not guide training or promotion decisions.

Deprecated does not mean delete immediately. It means the gate must not be used
as an active training objective or promotion blocker without a new manifest that
justifies reinstatement.

## M1185 Required Outputs

M1185 should produce:

```text
docs/m1185-paper-route-gate-utility-matrix-run.md
docs/gate-utility-matrix.md
runs/m1185_gate_utility_matrix/summary.json
runs/m1185_gate_utility_matrix/candidate_manifest.csv
runs/m1185_gate_utility_matrix/gate_utility_matrix.csv
runs/m1185_gate_utility_matrix/gate_stack_decisions.csv
```

The matrix can be built from existing artifacts and documented historical
outcomes. It should not run replay or training. If existing artifacts are too
incomplete, the output should say so and pre-register a candidate inventory
milestone.

## M1185 Acceptance Criteria

M1185 passes if:

- candidate classes contain good, known bad, near-miss, and null/no-op rows;
- gate stacks A/B/C are represented;
- each gate or corpus receives a provisional class and reason;
- known bad coverage and good false reject risk are reported;
- missing paths are explicit;
- no private holdout is used;
- no candidate replay, gate demotion, actor training, PPO, promotion, or
  actor-input change occurs.

M1185 fails if:

- it demotes gates as an action rather than recommendation;
- it lacks known bad candidates;
- it cannot distinguish `not_applicable` from pass/fail;
- it uses private holdout to tune the classification;
- it changes actor inputs or claims driver-performance progress.

## Follow-Up Routing

After M1185:

- if the matrix is complete, route to a separate gate cleanup design that
  updates active blocker policy without deleting historical tooling;
- if candidate inventory is insufficient, route to a candidate inventory
  milestone before any cleanup;
- if Stack C catches unique known bad candidates that A/B miss, keep the unique
  checks as `extended-regression` or `core`;
- if current proof rows are too lineage-specific for paper-route training, move
  them to `research-only` or `legacy` and introduce broader source-rich or
  finite-window comparison gates.

## What Is Not Claimed

M1184 does not claim:

- gate cleanup has happened;
- any historical gate is deprecated;
- any checkpoint is better;
- PPO is ready;
- source-rich proof exists;
- finite-window or GRU is superior;
- self-identification has been proven.

It only provides the audit design and the M1185 manifest.
