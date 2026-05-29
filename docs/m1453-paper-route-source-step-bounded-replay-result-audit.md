# M1453 Paper-Route Source-Step Bounded Replay Result Audit

## Summary

M1453 audits the M1452 source-step bounded replay smoke.

Decision:

```text
source_step_bounded_replay_audit_route_to_boundary_retarget_design
```

M1453 does not run replay, train, run PPO, promote, use private holdout, export
corpus, or change actor inputs.

## Evidence Summary

M1452 completed the first source-step bounded replay smoke:

```text
selected_candidate_rows: 64
actual_replay_rows: 192
history_positive_rows: 0
control_positive_rows: 0
normal_failed_rows: 120
candidate_step_column: source_step
geometry_aware_selector: true
```

The route is operational:

```text
source-step candidate anchoring is preserved;
geometry-aware replay selection works;
actual replay rows are emitted;
guardrails stay clean.
```

But the outcome evidence is negative:

```text
no history-positive rows;
no control-positive rows;
normal failure dominates the replay set.
```

## Supported Claims

M1452 supports these bounded claims:

```text
1. Source-step preflight-pass rows can be replayed without actor changes.
2. The replay probe preserves candidate_step_column == source_step.
3. The current source-step replay pressure is not yet producing history-positive terminal outcomes.
4. Action divergence alone is insufficient; terminal boundary alignment is still missing.
```

## Falsified or Blocked Claims

M1452 falsifies or blocks these claims:

```text
1. M1450 preflight-pass rows are immediately suitable as a training corpus.
2. Source-step action divergence plus forward geometry is enough to produce history-positive replay rows.
3. The project should proceed directly to corpus export, actor update, PPO, or promotion.
4. The negative result proves recurrent history is useless.
```

## Failure Taxonomy

Classification:

```text
scenario_sampling_failure
```

More specific description:

```text
source_step_replay_boundary_targeting_failure
```

Reason:

```text
120 / 192 rows fail or have negative normal margin under normal history.
The normal-viable rows do not create enough success-drop or margin-gap pressure.
```

This is a source/replay-pressure issue, not a self-ID falsification.

## Next Branch

Admit:

```text
m1454-paper-route-source-step-replay-boundary-retarget-design
```

The next design should target normal-viable near-boundary replay rows before any
training or corpus export. It should use M1452 actual replay rows to decide
which pressure controls matter:

```text
normal_success / normal_margin
variant_success / variant_margin
margin_gap
relocation geometry
history variant
candidate_step
capability pair
```

Potential retargeting directions:

```text
filter or mine for normal_success and low positive normal_margin;
avoid replay placements that are infeasible under normal history;
increase pressure only around normal-viable rows;
separate boundary retargeting from actor training.
```

## Guardrails

M1453 guardrail status:

```text
replay_started: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
training_corpus_exported: false
actor_input_contract_changed: false
level3_self_id_claim_made: false
```
