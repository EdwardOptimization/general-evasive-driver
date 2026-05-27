# M1090 V4 Public Base Source-Balanced Relocation Runner Implementation

## Purpose

M1090 implements the M1089 relocation-time source-balanced runner. This is an
infrastructure milestone only. It does not train, run PPO, promote a
checkpoint, use private holdout, or run the expensive M1091 relocation replay.

The milestone also formalizes a process-v5 self-identification evidence rule:
future manifests must state the self-ID claim level, current-frame substitution
risk, temporal evidence window, history-necessity tests, negative-result policy,
and allowed claims.

## Implemented Runner

Updated module:

```text
src/autodrift/source_balanced_boundary_relocation_surface.py
```

The module now has two modes:

```text
existing-artifact smoke:
  --candidate-csv + --boundary-rows-csv

full source-balanced relocation:
  --checkpoint-policy + --env-config + --outcome-csv
```

The full relocation path:

1. Reads the outcome CSV.
2. Builds the source-budget summary.
3. Selects relocation candidates with `select_source_balanced_candidates`.
4. Fails closed before replay if source budget or selected-candidate diversity
   is insufficient.
5. Loads each checkpoint policy and collects snapshots only for selected
   candidates assigned to that checkpoint label.
6. Calls `build_boundary_relocation_rows` with the selected candidates.
7. Marks balanced accepted wrong-history rows.
8. Writes raw boundary rows, balanced export rows, source-budget artifacts,
   robustness gates, and surface summary.

This fixes the M1089 blocker: balanced candidates now enter relocation replay
instead of being applied only as a post-filter over an old source-limited
boundary artifact.

## Fail-Closed Behavior

The runner intentionally refuses to replay when the source budget is not ready:

```text
decision: source_budget_not_ready
relocation_replay_started: false
```

It also refuses to replay when the selected candidate set cannot satisfy the
configured source-balance quotas:

```text
decision: source_balanced_candidates_not_ready
relocation_replay_started: false
```

This keeps M1091 from silently becoming another source-unaware relocation run.

## Artifact Schema

Both full relocation and existing-artifact smoke write:

```text
summary.json
source_budget_summary.json
source_budget_rows.csv
balanced_candidate_rows.csv
candidate_balance_rejection_rows.csv
boundary_relocation_rows.csv
balanced_accepted_wrong_history_rows.csv
balance_rejection_rows.csv
robustness_gates.csv
```

Full relocation also writes:

```text
surface_summary.csv
```

The raw `boundary_relocation_rows.csv` remains the replay audit trail. Only
`balanced_accepted_wrong_history_rows.csv` is eligible for later compact corpus
conversion.

## Process-V5 Self-ID Evidence Rule

Added formal document:

```text
docs/self-identification-evidence-discipline.md
```

Added validator constants and checks:

```text
src/autodrift/research_schema.py
src/autodrift/research_validate.py
tests/test_research_validate.py
```

From priority `10850` onward, manifests must include:

```text
self_id_evidence_discipline
```

with fields:

```text
claim_level
current_frame_substitution_risk
history_necessity_tests
temporal_evidence_window
negative_result_policy
allowed_claims
```

Allowed claim levels:

```text
not_applicable
level0_no_adaptation
level1_closed_loop_reactive
level2_history_encoded_reactive
level3_anticipatory_self_identification
```

The rule prevents broad closed-loop success or fixed public proof rows from
being mislabeled as self-identification. Future manifests must state whether
they are testing current-frame reactivity, history-encoded reactivity, or
anticipatory self-ID.

## Validation

Focused tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_research_validate.py \
  tests/test_source_balanced_boundary_relocation_surface.py \
  tests/test_wrong_history_boundary_relocation_surface.py \
  tests/test_boundary_wrong_history_surface_robustness.py
```

Result:

```text
48 passed
```

Research validation:

```text
make research-validate
```

Result:

```text
research validation passed
process_v5_from_priority=10850
```

## Decision

```text
source_balanced_relocation_runner_implementation_admit_m1091_run
```

Next:

```text
m1091-v4-public-base-source-balanced-boundary-relocation-run
```

M1091 is the first actual source-balanced relocation replay run. It must remain
evaluation-only: no PPO, no actor training, no promotion, no private holdout,
and no threshold weakening.
