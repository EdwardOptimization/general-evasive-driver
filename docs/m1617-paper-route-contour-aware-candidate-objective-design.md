# M1617 Paper-Route Contour-Aware Candidate Objective Design

## Summary

M1617 designs objective semantics for the M1615 contour-aware candidate corpus
package.

Decision:

```text
contour_aware_candidate_objective_design_admit_audit_and_synthesis
```

This milestone is design-only. It does not construct a loss, does not write an
objective config, does not update an actor, does not run PPO, does not promote a
checkpoint, and does not use private holdout.

## Inputs

The only objective-design inputs are the audited public package from M1615 and
the M1616 audit:

```text
runs/m1615_contour_aware_candidate_corpus/summary.json
runs/m1615_contour_aware_candidate_corpus/corpus_manifest.json
runs/m1615_contour_aware_candidate_corpus/positive_candidate_rows.csv
runs/m1615_contour_aware_candidate_corpus/diagnostic_guardrail_rows.csv
runs/m1615_contour_aware_candidate_corpus/role_summary.csv
runs/m1615_contour_aware_candidate_corpus/source_edge_summary.csv
runs/m1615_contour_aware_candidate_corpus/guardrail_summary.csv
docs/m1616-paper-route-contour-aware-candidate-corpus-export-result-audit.md
```

Observed package facts:

```text
positive_candidate_count: 39
diagnostic_guardrail_count: 232
positive_rows_all_clean: true
diagnostic_rows_used_as_positive: false
source_edge_count: 4
max_source_edge_share: 0.3333333333333333
training_ready: false
public_proof_artifact: true
paper_level_claim_supported: false
level3_self_id_claim_supported: false
```

## Objective Roles

The objective must preserve three role boundaries.

### Positive Candidates

Rows in `positive_candidate_rows.csv` are the only rows eligible for a future
positive candidate residual.

They represent public proof candidates selected by the contour-aware clean
active-set route:

```text
corpus_role: positive_candidate
role_weight: 1.0
label: history_control_separated
rule_bucket: primary
rule_reason: clean_edge_window_primary
training_ready: false
```

Future implementations may evaluate whether a checkpoint preserves or improves
the candidate history/control separation metrics on these rows. That evaluation
is not yet a training loss and is not closed-loop proof by itself.

### Diagnostic Guardrails

Rows in `diagnostic_guardrail_rows.csv` are never positive targets.

They are role-integrity and overfit guardrails:

```text
corpus_role: diagnostic_guardrail
role_weight: 0.0
allowed_as_positive: false
```

Diagnostics may be used only to check that a future evaluator or objective does
not relabel dominated/control-only/null rows into positive candidates. They
must not contribute positive improvement to an aggregate objective.

### Metadata Guardrails

The package metadata remains binding:

```text
public_proof_artifact: true
private_holdout_used: false
paper_level_claim_supported: false
level3_self_id_claim_supported: false
training_ready: false
requires_objective_design_before_training: true
```

Any future evaluator must carry these flags into its output summary.

## Lexicographic Semantics

Acceptance must be lexicographic rather than scalar-only. A lower scalar score
cannot override role or metadata violations.

Order:

1. Role and metadata integrity.
2. Diagnostic guardrails remain non-positive.
3. Positive candidate exact evaluator is finite and full-corpus.
4. Only after a separate audit may an objective-only update be designed.
5. Training, PPO, promotion, private holdout, and paper-level claims remain
   blocked.

The diagnostic rows are guardrails, not negative examples that can be optimized
against in this milestone. If a later design wants diagnostics to become an
explicit negative objective, that must be separately designed and audited.

## Exact Evaluator Requirement

After the required design audit/synthesis, a later implementation milestone
should implement a no-update exact evaluator over the M1615 package.

Minimum future evaluator behavior:

```text
read positive_candidate_rows.csv
read diagnostic_guardrail_rows.csv
verify corpus_manifest.json role metadata
write per-positive candidate rows
write per-diagnostic guardrail rows
write role-integrity summary
write source-edge summary
write exact objective summary
write guardrail summary
do not mutate checkpoint weights
do not write a checkpoint
do not write a training corpus
do not write objective_config.json or loss_config.json
```

The evaluator should be called an evaluator or sanity checker, not an optimizer.
It may define exact measurable residuals such as positive candidate gap,
history-control separation, role-weight accounting, and diagnostic contamination
counts, but it must not run gradient updates.

## Future Evaluator Public Gates

The future evaluator should pass only if:

```text
exact_evaluator_implemented == true
candidate_objective_evaluated == true
objective_constructed == false
loss_constructed == false
training_corpus_exported == false
positive_candidate_count == 39
diagnostic_guardrail_count == 232
diagnostic_rows_used_as_positive == false
diagnostic_positive_weight_sum == 0.0
positive_rows_all_clean == true
role_metadata_verified == true
public_proof_metadata_complete == true
all_objective_metrics_finite == true
checkpoint_weights_mutated == false
training_started == false
ppo_used == false
promoted == false
private_holdout_used == false
actor_input_contract_changed == false
labels_enter_actor_input == false
level3_self_id_claim_made == false
guardrail_violation_count == 0
```

The future evaluator may report baseline checkpoint policy-side metrics if the package has
enough information to evaluate them. If the available package only supports
metadata and row-metric residuals, the evaluator should report that limitation
explicitly instead of fabricating action-logprob objectives.

## Unsupported Claims

M1617 does not support:

```text
the objective has been implemented;
the objective improves any checkpoint;
PPO is admitted;
candidate rows are training-ready;
diagnostics are negative training targets;
closed-loop behavior improved;
the driver has level3 self-identification;
paper-level evidence has been produced.
```

## Public-Gate Overfit Risk

Risk remains high:

```text
the candidate set has only 39 public positives;
the source-edge count is 4;
diagnostic rows are public guardrails, not private validation;
an optimizer could overfit the package without improving closed-loop driving.
```

Mitigation:

```text
M1618 is no-update evaluator only;
diagnostics are lexicographic guardrails, not scalar positives;
any future optimizer requires a separate audit after M1618;
private holdout remains unused and protected.
```

## M1618 Audit And Synthesis Requirement

M1618 must be a process audit/synthesis milestone before implementation. It
should check:

```text
M1617 did not construct an objective or loss;
M1617 did not route directly to training/PPO/promotion;
M1617 keeps diagnostics non-positive;
M1617's future evaluator requirements are explicit;
branch cadence is satisfied before further narrow implementation.
```

M1618 may admit the no-update evaluator implementation as the next branch step
only if the audit confirms these conditions.

## Decision

Admit one post-design audit/synthesis milestone:

```text
m1618-paper-route-contour-aware-candidate-objective-design-audit-and-synthesis
```

Do not route directly to actor update, PPO, promotion, private holdout, or
paper-level claims.
