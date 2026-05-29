# M1608 Paper-Route Clean Active-Set Contour Mapping Branch Synthesis

## Summary

M1608 synthesizes the M1598-M1607 clean active-set contour mapping branch before
another implementation.

Decision:

```text
clean_active_set_contour_mapping_synthesis_continue_to_diagnostic_complete_replay
```

The branch should continue to exactly one label-blind diagnostic-complete
bounded replay. This is not a promotion, materialization, training, or PPO
decision. It is the smallest admissible test after M1605 showed primary contour
replay survived but the capped diagnostic sample was too weak.

## evidence_summary

M1598 designed an offline contour mapper over existing public artifacts instead
of running another replay.

M1599 implemented the mapper:

```text
enriched rows: 528
clean rows: 51
strongest contour: clean_edge_window
```

M1600 audited that map and admitted contour-aware source-rule design.

M1601 designed a strict primary rule:

```text
primary contour: clean_edge_window
primary source edges: four source edges only
diagnostics: endpoint-neighbor, negative, and mixed/dominated exclusions
```

M1602 implemented the rule:

```text
primary rows: 144
primary clean rows: 39
primary clean source edges: 4
max primary clean source-edge share: 0.3333333333333333
diagnostic rows: 232
```

M1603 audited the offline selector pass and admitted bounded replay design.

M1604 designed one replay over all 144 primary rows plus a reason-capped
diagnostic sample.

M1605 implemented that replay. A replay-id collision was found and fixed by
using `source_run::pair_id`. After the fix, the result was split:

```text
primary replay directed pairs: 144
diagnostic replay directed pairs: 96
primary clean directed pairs: 39
primary clean source edges: 4
max primary clean source-edge share: 0.3333333333333333
diagnostic dominated/control count: 35
diagnostic clean share: 0.0
passes public smoke gates: false
null result classification: diagnostic_control_failure
```

The primary contour survived replay, but the capped diagnostic sample did not
preserve enough negative/control evidence.

M1606 audited the split result and admitted a design-only diagnostic-complete
repair.

M1607 designed that repair:

```text
primary replay rows: all 144
diagnostic replay rows: all 232
diagnostic per-reason cap: 999
expected intervention rows: 3008
label-based diagnostic selection: forbidden
```

M1607 could not route directly to implementation because the workflow synthesis
cadence fired for the current branch.

## supported_claims

M1608 supports:

```text
clean_edge_window is a useful public contour selector;
M1602 produced a strict primary contour with 144 rows and 39 clean rows;
M1605 preserved that primary contour under bounded replay;
M1605 diagnostic failure was isolated to capped diagnostic coverage, not primary collapse;
M1607 pre-registered a label-blind full-diagnostic replay;
one diagnostic-complete replay is justified before another audit.
```

## falsified_claims

M1608 falsifies:

```text
a primary contour replay pass is sufficient without diagnostic controls;
the 96-row capped diagnostic sample was enough to characterize diagnostics;
another implementation can proceed after 10 branch milestones without synthesis.
```

## unsupported_claims

M1608 does not support:

```text
candidate materialization;
training corpus export;
PPO continuation;
checkpoint promotion;
private-holdout evidence;
paper-level self-identification;
level3 anticipatory self-identification.
```

## failure_taxonomy_summary

```text
scenario_sampling_failure
objective_overfit
metric_artifact
```

`scenario_sampling_failure` covers the M1605 capped diagnostic shortfall.
`objective_overfit` remains the branch risk because the contour is still a
public-row artifact. `metric_artifact` covers the M1605 replay-id collision,
which was fixed before interpreting the final result.

## public_gate_overfit_risk

Risk:

```text
medium_high
```

Reasons:

```text
M1599-M1607 all operate on public contour and replay artifacts;
M1602/M1605 prove a primary contour but not broad distribution behavior;
diagnostic-complete replay is still a public proof diagnostic, not private evidence.
```

Mitigations:

```text
use all diagnostic rows instead of label-selected diagnostics;
keep selector thresholds unchanged;
block materialization, corpus export, training, PPO, promotion, and private-holdout claims;
route to audit whether the diagnostic-complete replay passes or fails.
```

## next_branch_decision

Continue the same branch for exactly one bounded implementation:

```text
m1609-paper-route-diagnostic-complete-bounded-replay-implementation
```

M1609 should run:

```text
PYTHONPATH=src python -m autodrift.contour_aware_bounded_replay --output-dir runs/m1609_diagnostic_complete_bounded_replay --diagnostic-per-reason-cap 999
```

M1609 must not materialize candidates, export a training corpus, train, run PPO,
promote, use private holdout, change actor inputs, relax thresholds, select
diagnostics by labels, or claim level3 self-identification.

## Guardrails

```text
replay_started: false in M1608
history_interventions_executed: false in M1608
candidate_materialized: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
training_corpus_exported: false
labels_enter_actor_input: false
level3_self_id_claim_made: false
```

## Next

```text
m1609-paper-route-diagnostic-complete-bounded-replay-implementation
```
