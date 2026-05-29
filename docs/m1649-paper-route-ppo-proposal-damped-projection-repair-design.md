# M1649 Paper-Route PPO-Proposal Damped Projection Repair Design

## Summary

M1649 designs the transition from controlled actor_mean perturbation repair to
proposal-delta repair.

Decision:

```text
proposal_repair_design_admit_no_checkpoint_source_preflight
```

The branch should not repair a checkpoint yet. The immediate next step should
be a no-checkpoint proposal-source preflight that identifies branch-compatible
proposal deltas, measures exact contour-aware residuals, records trust-region
metadata, and selects one or more repair candidates for a later no-checkpoint
repair probe.

This milestone does not run PPO, train, run projection, repair a proposal, run
closed-loop evaluation, write checkpoint artifacts, promote, use private
holdout, change actor inputs, treat diagnostics as positive targets, treat
donor-plus actions as loss targets, or claim paper-level or level3
self-identification evidence.

## Starting Point

Current public-gate base:

```text
runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
```

Contour-aware materialized target tensors:

```text
runs/m1630_contour_aware_full_target_materialization
```

Latest projection evidence:

```text
M1643: one controlled actor_mean damped repair pass, reduction ratio 0.8982656378486144
M1646: 9/9 fixed-grid controlled actor_mean perturbations repaired
M1648: local projection branch closed and promoted to this proposal-repair design branch
```

Important limitation:

```text
M1646 repaired synthetic actor_mean perturbations, not a real PPO/proposal
checkpoint delta.
```

## Proposal Source Policy

There is no branch-local PPO proposal selected for this contour-aware route yet.
Therefore M1650 should not jump directly to PPO or checkpoint repair. It should
first run a no-checkpoint proposal-source preflight.

Allowed proposal sources for the first preflight:

```text
source group A: M1362 interpolation candidates from the current public-base lineage
source group B: future branch-local PPO proposals only if a manifest explicitly records parent base == M1362 alpha 0.1
```

Blocked in the first preflight:

```text
historical PPO checkpoints from unrelated older bases;
private holdout candidates;
untracked local checkpoints;
any checkpoint whose actor input contract differs from P0 human-view no-wheel 72-dim online-GRU.
```

M1362 has a useful proposal source table:

```text
runs/m1362_bidirectional_active_set_interpolation_preflight/candidate_checkpoints.csv
runs/m1362_bidirectional_active_set_interpolation_preflight/alpha_summary.csv
```

Candidate roles:

```text
base anchor:
  alpha 0.1

smaller-control alphas:
  0.005, 0.01, 0.02, 0.05

larger proposal alphas:
  0.2, 0.4, 0.6, 0.8, 1.0
```

The larger proposal alphas are especially useful because they are real
same-line checkpoint deltas, not synthetic perturbations. The M1362 preflight
already shows they can improve exact source-history metrics while failing
public replay gates:

```text
alpha 0.2: M183/M170 failed, preflight_pass false
alpha 0.4: M183/M170 failed, preflight_pass false
alpha 0.6: M183/M170 failed, preflight_pass false
alpha 0.8: M183/M170 failed, preflight_pass false
alpha 1.0: M267/M264 and M183/M170 failed, preflight_pass false
```

That makes them appropriate public proposal stressors for preflight. They are
not PPO proposals, so M1650 must label them as `same_line_interpolation`
proposals. PPO-proposal repair remains a later application once a branch-local
PPO proposal exists.

## M1650 No-Checkpoint Preflight Design

M1650 should implement a proposal-source preflight, not a repair.

Input:

```text
base checkpoint:
  runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt

proposal source table:
  runs/m1362_bidirectional_active_set_interpolation_preflight/candidate_checkpoints.csv

alpha metrics:
  runs/m1362_bidirectional_active_set_interpolation_preflight/alpha_summary.csv

materialized target tensors:
  runs/m1630_contour_aware_full_target_materialization
```

Output artifacts:

```text
runs/m1650_proposal_source_preflight/summary.json
runs/m1650_proposal_source_preflight/candidate_summary.csv
runs/m1650_proposal_source_preflight/guardrail_summary.csv
```

For each candidate, M1650 should record:

```text
candidate_id
proposal_source_type
checkpoint
is_base_anchor
branch_compatible
actor_input_contract_changed
forbidden_parameter_mutation_detected
log_std_l2_to_base
parameter_l2_to_base
parameter_max_abs_to_base
actor_mean_l2_to_base
non_actor_mean_l2_to_base
positive_exact_residual_mean
positive_policy_action_residual_l2_max
diagnostic_policy_action_residual_l2_max
diagnostic_rows_used_as_positive
donor_plus_action_used_as_loss_target
m1362_preflight_pass
m267_m264_gate_pass
m183_m170_gate_pass
repair_candidate_role
```

Expected roles:

```text
base_anchor:
  alpha 0.1

control_pass:
  compatible smaller alphas whose public gates passed

repair_candidate:
  compatible larger alphas with measurable contour-aware exact residual and
  known public-gate failure

excluded:
  missing, contract-violating, or lineage-incompatible candidates
```

M1650 may select repair candidates only as metadata:

```text
selected_repair_candidate_count >= 1
```

It must not repair them.

## Repair Objective For Later Milestones

After M1650 identifies proposal candidates, a later no-checkpoint repair probe
may use the M1646 damped projection rule with stricter proposal guards.

The first repair probe should start from a selected proposal checkpoint and
only optimize:

```text
actor_mean.weight
actor_mean.bias
```

Frozen:

```text
response encoder
context encoder
GRU
fusion layers
critic
log_std
auxiliary heads
all non-actor_mean parameters
```

Initial candidate:

```text
full proposal weights, with only actor_mean allowed to move during repair
```

Exact objective:

```text
positive rows:
  correct hidden -> preferred_action
  wrong hidden   -> wrong_history_action
  separation-collapse residual

diagnostic rows:
  evaluated only
  zero positive weight
  no gradient

donor_plus_hidden_action:
  diagnostic-only
  never a loss target
```

Acceptance for no-checkpoint repair:

```text
measurable initial residual
positive exact residual reduced
diagnostic guardrails clean
actor input contract unchanged
non-actor_mean parameter delta from proposal unchanged
no checkpoint artifact written
no training/PPO/promotion/private holdout used
```

If actor_mean-only repair cannot reduce a real proposal residual, classify the
result as scope-limited rather than tuning in place. The next design may then
consider a wider but still pre-registered trainable scope.

## Acceptance Order

The branch order should be:

```text
1. M1650 no-checkpoint proposal-source preflight.
2. Result audit.
3. No-checkpoint selected-proposal repair design or implementation.
4. Exact objective gate.
5. Result audit.
6. Only then consider checkpoint artifact design.
7. Only after checkpoint artifact design, run first replay gates.
8. Only after replay/behavior/generalization gates, consider promotion.
```

Exact contour-aware objectives are pre-replay feasibility checks. They are not
closed-loop behavior, paper-level, private-holdout, or promotion evidence.

## Failure Taxonomy

Use:

```text
lineage_invalid:
  candidate checkpoint is not compatible with M1362 alpha 0.1 or has unclear parentage

contract_violation:
  actor input contract changes or labels enter actor input

metric_artifact:
  sampled or metadata metrics look useful but exact residuals do not support repair

objective_overfit:
  exact residuals improve but replay/proof gates later fail

proof_washout:
  repaired candidate later loses wrong-history/proof behavior

training_instability:
  projection optimizer step is connected but unstable

none:
  clean design or clean preflight
```

## Public-Gate Overfit Control

M1650 should not choose a candidate by optimizing the M1630 exact tensors. It
should only report source availability and candidate roles.

Rules:

```text
do not tune thresholds after seeing M1650 exact residuals;
do not write repaired checkpoints;
do not discard candidates only because exact residuals are inconvenient;
include both pass controls and failed larger proposals;
separate public-gate failures from exact-objective residuals;
route to audit before repair.
```

## Next Route

Admit:

```text
m1650-paper-route-proposal-source-preflight-implementation
```

M1650 should implement and run the no-checkpoint source preflight described
above. It should not run PPO, train, run projection, repair a proposal, write
checkpoint artifacts, run closed-loop evaluation, promote, use private holdout,
change actor inputs, or claim paper-level or level3 self-ID evidence.
