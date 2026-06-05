# M2777 Engineering Controller Route A Source-Only Action-Response Belief Intervention Branch Synthesis

## Metadata

- status: completed
- synthesis decision: `pivot`
- next branch decision: `pivot_to_route_a_source_only_belief_stress_training_protocol_design`
- manifest: `experiments/manifests/m2777-engineering-controller-route-a-source-only-action-response-belief-intervention-branch-synthesis.json`
- synthesis artifact: `docs/m2777-engineering-controller-route-a-source-only-action-response-belief-intervention-branch-synthesis.md`
- parent audit: `docs/m2776-engineering-controller-route-a-source-only-action-response-belief-intervention-delta-panel-materialization-result-audit.md`
- parent summary: `runs/m2775_engineering_controller_route_a_source_only_action_response_belief_intervention_delta_panel_materialization/summary.json`
- route plan: `docs/post-m2470-route-plan.md`
- self-ID route plans: `docs/self-id-go-no-go-paper-route-plan.md`, `docs/paper-route-finite-window-vs-gru-plan.md`
- follow-up manifest: `experiments/manifests/m2778-engineering-controller-route-a-source-only-belief-stress-training-protocol-design.json`
- next: `m2778-engineering-controller-route-a-source-only-belief-stress-training-protocol-design`

## Evidence Summary

M2772-M2776 completed a source-only Route A action-response belief
intervention branch:

```text
M2772 design:
  admitted a repo-local source-only HF0/FourWheel intervention surface
  admitted 32 role/axis/seed candidate rows for M2773
  specified normal recurrent, reset-hidden, zero-command-history, and
  held-actuator-history conditions
  preserved M2771 negative current-sim repair context and M2638 HF3 blocker

M2773 materialization:
  status_pass: true
  gate_matrix_pass: true
  candidate rows: 32
  intervention conditions: 4
  candidate/intervention rows: 128
  execution rows: 128
  failure rows: 0
  action-response trace rows: 10240
  mitigation reference guard rows: 8
  actor guard rows: 7
  claim boundary rows: 13
  gate rows: 21

M2774 audit:
  accepted M2773 completeness and claim safety
  rejected direct performance, ranking, validation, paper, current-sim,
  high-fidelity, full-driver, and self-ID interpretation

M2775 delta panel:
  status_pass: true
  gate_matrix_pass: true
  normal execution rows: 32
  evaluator intervention execution rows: 96
  delta rows: 96
  role/dynamics aggregate rows: 24
  intervention-condition aggregate rows: 3
  matched trace pair rows: 7680
  missing pairs: 0
  duplicate execution pairs: 0
  mitigation reference guard rows: 8
  actor guard rows: 7
  claim boundary rows: 17
  gate rows: 24

M2776 audit:
  accepted M2775 completeness and claim safety
  rejected direct interpretation
  routed to branch synthesis
```

The branch changed the evidence state by making action-response and recurrent
history interventions auditable under the deployable 72/3 actor contract. It
did not change the driver-performance state enough to admit validation,
ranking, promotion, paper evidence, high-fidelity evidence, full-driver
completion, or level3 self-identification.

M2775 provides modest but nonzero source-only sensitivity:

```text
collision added delta rows: 0
collision removed delta rows: 0
road-departure added delta rows: 0
road-departure removed delta rows: 4
minimum obstacle clearance delta mean: 0.0142847055
minimum road margin delta mean: 0.0630051182
trace delta proxy delta mean: 1.2601287073
command response proxy delta mean: 0.0482557083
action L1 mean: 0.0383708570
physical action L1 mean: 0.0383708570
ego response L2 mean: 0.1288659872
state speed absolute delta mean: 0.0388064204
```

The intervention-condition aggregates are useful for route design, not for
ranking:

```text
reset_hidden_each_step:
  delta rows: 32
  road-departure removed: 2
  road-departure added: 0
  collision added: 0
  collision removed: 0
  action L1 mean mean: 0.0458961727
  ego response L2 mean mean: 0.1494829167

zero_previous_command_history:
  delta rows: 32
  road-departure removed: 1
  road-departure added: 0
  collision added: 0
  collision removed: 0
  action L1 mean mean: 0.0315376361
  ego response L2 mean mean: 0.1060846080

held_actuator_history:
  delta rows: 32
  road-departure removed: 1
  road-departure added: 0
  collision added: 0
  collision removed: 0
  action L1 mean mean: 0.0376787622
  ego response L2 mean mean: 0.1310304369
```

M2773 also preserves weak behavior-quality accounting:

```text
collision diagnostic rows: 32
road-departure diagnostic rows: 68
```

Those rows remain diagnostic accounting only. They are not a success-rate
verdict and must not be hidden by the four road-departure removals in M2775.

## Supported Claims

M2777 supports these bounded claims:

```text
M2772-M2776 form a complete claim-safe source-only action-response belief
intervention branch.

M2773 materialized all registered source-only HF0/FourWheel intervention rows
with 0 execution failure rows and complete trace accounting.

M2775 materialized complete normal-vs-intervention delta artifacts over 96
paired evaluator intervention rows and 7680 matched trace pairs.

The branch preserved P0 observation shape 72, action shape 3, deployed
steer/throttle/brake action semantics, no hidden/oracle actor input, no
actor-visible role/dynamics/intervention/outcome/progress/success/verdict
labels, and mitigation reference guards outside ordinary denominators.

Source-only history and recurrent-state interventions can measurably perturb
action-response traces and some road-departure diagnostics.

The source-only deltas are strong enough to justify a new Route A protocol that
turns them into a bounded belief-stress training/admission design.
```

These claims support a route decision only. They do not support repair success,
driver performance, validation readiness, validation result, ranking, winner
selection, checkpoint promotion, success-rate verdict, paper evidence,
finite-window-vs-GRU conclusion, current-sim verdict, high-fidelity validation,
full ideal driver completion, or level3 self-identification.

## Falsified Claims

The following claims are rejected or not admitted:

```text
M2775 proves driver performance: false
M2775 proves repair success: false
M2775 admits validation readiness: false
M2775 validates current-sim behavior: false
M2775 validates high-fidelity behavior: false
M2775 ranks intervention conditions: false
M2775 selects a winner or promotes a checkpoint: false
M2775 proves finite-window-vs-GRU evidence: false
M2775 proves level3 self-identification: false
M2775 completes the full ideal driver gate: false
M2775 justifies another no-new-data source-only reanalysis as the next main
research action: false
```

The source-only delta branch also falsifies a weaker process claim: repeating
the same delta-accounting surface is not the right next step. M2773 and M2775
already made the source-only intervention evidence complete and auditable. The
next branch must change the evidence surface, stop, or pivot.

## Failure Taxonomy Summary

Controlled failures and risks:

```text
contract_violation:
  controlled. Actor observation/action remains 72/3, labels remain
  actor-invisible, and no hidden/oracle actor input is admitted.

lineage_invalid:
  controlled. M2772-M2776 docs, manifests, summaries, CSV artifacts, and
  route plans are traceable.

metric_artifact:
  controlled by interpretation. M2775 delta metrics are preserved as
  source-only diagnostics, not success-rate verdict metrics.

proof_washout:
  controlled. Mitigation reference rows remain guarded outside ordinary
  denominators.
```

Active failures and risks:

```text
behavior_regression:
  active. M2773 records 32 collision diagnostic rows and 68 road-departure
  diagnostic rows, and M2775 removes only 4 road-departure diagnostics across
  96 delta rows with no collision changes.

scenario_sampling_failure:
  active. The branch is source-only HF0/FourWheel evidence and not a fresh
  validation distribution or high-fidelity validation layer.

objective_overfit:
  high if Route A performs another no-new-data source-only delta reanalysis,
  ranks intervention rows, or packages M2775 as a verdict.

local_search:
  active if the branch keeps materializing audits of the same completed source
  rows instead of creating fresh closed-loop/training evidence or stopping.
```

## Public-Gate Overfit Risk

Public-gate overfit risk is high if the next action is:

```text
another M2775-like source-only delta reanalysis
ranking reset-hidden versus zero-command-history versus held-actuator-history
claiming success-rate improvement from 4 road-departure removals
hiding M2773 collision and road-departure diagnostic accounting
weakening mitigation-reference denominators
using source-only rows as paper, current-sim, high-fidelity, or self-ID proof
training immediately without a protocol that separates diagnostics, admission
gates, and later closed-loop evidence
```

Risk is lower if Route A pivots to a protocol that uses M2775 only as an
admission signal for the next evidence surface. That protocol should define how
source-only belief-stress rows, history-intervention deltas, actor guards,
claim guards, and later training/evaluation admission criteria connect to a
future bounded materialization or execution milestone. It must still preserve
the post-M2470 split: Route A may pursue an engineering controller baseline,
while Route B self-ID and finite-window-vs-GRU claims require a fair
controller-family matrix, and Route C high-fidelity work remains gated by the
source dependency boundary.

## Next Branch Decision

M2777 chooses:

```text
pivot_to_route_a_source_only_belief_stress_training_protocol_design
```

Rejected alternatives:

```text
continue same source-only intervention/delta reanalysis:
  Rejected. M2773/M2775 already completed the materialization and delta
  accounting; another no-new-data reanalysis would mainly add process overhead.

direct training or PPO continuation:
  Premature. M2775 is source-only diagnostic evidence. A training admission
  protocol must first specify stress rows, curriculum/admission gates,
  actor/claim guards, negative-result handling, and how future fresh evidence
  would be separated from source-only diagnostics.

package-with-limitations:
  Useful later, but it would freeze a weak diagnostic state rather than moving
  the engineering driver toward a usable closed-loop baseline.

defer-to-Route-B:
  Not the immediate Route A next step. Route B still needs a separately
  pre-registered L0/L1/L2/L3 fair controller-family matrix and must not treat
  M2775 as self-ID or finite-window-vs-GRU evidence.

defer-to-Route-C:
  Route C remains important, but direct HF3 execution is still blocked by the
  M2638 source dependency. Route C should not be used to hide the current
  source-only behavior limitations.

stop:
  Too early. The branch produced modest but real source-only sensitivity, so a
  bounded protocol that can change the future evidence surface is justified.
```

Admitted follow-up:

```text
m2778-engineering-controller-route-a-source-only-belief-stress-training-protocol-design
```

M2778 must be design-only. It should define a bounded Route A source-only
belief-stress training/admission protocol that can later admit a materialized
training pack, short PPO continuation, or stop decision only under separately
registered follow-up evidence. It must not reset, step, run policy actions,
roll out, replay, validate, train, run PPO, build source, probe adapters, run
external simulation, rank conditions/controllers, select a winner, promote a
checkpoint, compute success-rate verdicts, or make repair-success,
driver-performance, paper, current-sim, high-fidelity, full-driver, or self-ID
claims.

## Claim Boundary

Allowed M2777 claim:

```text
M2772-M2776 completed a claim-safe source-only action-response belief
intervention branch, and the branch should pivot to a bounded Route A
belief-stress training protocol design before any further reanalysis,
execution, training, ranking, validation, or paper/self-ID claim.
```

Rejected claims:

```text
repair success
driver performance
validation readiness or result
controller-family ranking
intervention-condition ranking
winner selection
checkpoint promotion
success-rate verdict
paper evidence
finite-window-vs-GRU conclusion
current-sim verdict
high-fidelity validation readiness or result
full ideal driver completion
level3 self-identification
```
