# M2841 Engineering Controller Post Route C HF3 Stop Fresh Source-Diverse Closed-Loop Evidence Synthesis Selected Next Route Design

## Metadata

- status: completed
- decision: `admit_route_a_driver_like_recurrent_belief_architecture_training_redesign_design`
- manifest: `experiments/manifests/m2841-engineering-controller-post-route-c-hf3-stop-fresh-source-diverse-closed-loop-evidence-synthesis-selected-next-route-design.json`
- design artifact: `docs/m2841-engineering-controller-post-route-c-hf3-stop-fresh-source-diverse-closed-loop-evidence-synthesis-selected-next-route-design.md`
- parent synthesis: `docs/m2840-engineering-controller-post-route-c-hf3-stop-fresh-source-diverse-closed-loop-evidence-result-synthesis.md`
- parent audit: `docs/m2839-engineering-controller-post-route-c-hf3-stop-fresh-source-diverse-closed-loop-evidence-result-audit.md`
- parent summary: `runs/m2838_engineering_controller_post_route_c_hf3_stop_source_diverse_closed_loop_evidence_preflight/summary.json`
- route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2842-engineering-controller-route-a-post-hf3-stop-negative-evidence-architecture-redesign-or-freeze-result-audit.json`
- next: `m2842-engineering-controller-route-a-post-hf3-stop-negative-evidence-architecture-redesign-or-freeze-result-audit`

## Design Decision

M2841 selects a Route A architecture/training redesign path:

```text
admit_route_a_driver_like_recurrent_belief_architecture_training_redesign_design
```

This is a design-only route decision. M2841 does not reset, step, roll out,
replay, validate, train, run PPO, build source, probe adapters, rank, select a
winner, promote a checkpoint, or claim driver performance.

The decision rejects three lower-leverage continuations:

```text
limited-baseline freeze as the immediate next route:
  rejected for now. It is useful as a fallback/package boundary, but it would
  freeze a controller after M2838 shows 1 success, 2 collisions, and 13
  off_track rows. That does not move the long-term driver objective.

another M2838-like source-diverse closed-loop execution:
  rejected. M2838 is complete and weak/negative; repeating the same evidence
  axis would be local search unless the controller architecture, training
  recipe, source distribution, or claim boundary changes first.

direct Route C/HF3 retry:
  rejected. M2638 and M2836 keep Route C/HF3 stopped until valid source,
  approved dependency acquisition, package route, or alternate backend
  contract is supplied.
```

Route B paper/self-ID work remains deferred until a separately pre-registered
fair controller-family matrix exists. M2841 does not admit a self-ID claim.

## Evidence Used

M2837-M2840 provide the immediate route evidence:

```text
M2837:
  selected a fresh Route A closed-loop diagnostic surface after Route C/HF3
  stopped

M2838:
  status_pass: true
  selected rows: 16
  resolved rows: 16
  execution rows: 16
  failure rows: 0
  diagnostic success: 1
  diagnostic collision: 2
  diagnostic off_track: 13
  prior unique task_source ids: 43
  actor contract: 72 observation / 3 action, no hidden/oracle actor input

M2839:
  accepted M2838 as complete and claim-safe diagnostic evidence only

M2840:
  synthesized the branch and selected architecture-redesign-or-freeze design
  rather than same-surface execution or Route C/HF3 retry
```

Additional Route A context keeps the redesign bounded:

```text
M2771:
  scalar actor-head bias repair branch was complete and negative, so another
  actor-head bias sweep is not admitted

M2786/M2800:
  source-only belief-stress and corrective-training branches produced bounded
  candidate or training artifacts, but none admitted promotion, validation, or
  driver-performance claims

post-M2470 route plan:
  Route A should freeze a usable actuator-level active-safety baseline only
  with explicit failure taxonomy, while current-sim diagnostics must not become
  the whole research loop
```

## Selected Redesign Scope

The next evidence-changing route should be an architecture/training redesign
design under the same deployable actor input contract.

Allowed design axes for the later redesign route:

```text
recurrent belief/state architecture:
  change internal latent/recurrent structure, memory horizon, recurrent update,
  or belief regularization without adding actor-visible oracle inputs

training recipe:
  redesign curriculum, loss weighting, sequence sampling, closed-loop
  correction, proof/generalization/promotion gates, and negative-failure
  retention

source distribution:
  choose new source-only or current-sim training/evaluation surfaces only after
  pre-registering proof and generalization separation

failure taxonomy integration:
  use M2838 off_track/collision rows as evaluator-side admission evidence, not
  actor-visible labels or reward shortcuts
```

Forbidden design shortcuts:

```text
do not add mu mass tire stiffness brake scale actuator tau slip tire force TTC
required clearance oracle stopping distance AEB/AES/drift labels controller
mode route labels success/progress labels or verdict labels to actor input

do not reuse scalar actor-head bias repair as the main redesign
do not tune only one public profile and compare it directly to previous rows
do not collapse proof generalization and promotion gates
do not promote a checkpoint from one diagnostic surface
do not compute a success-rate verdict from M2838 rows
```

## Required M2842 Audit

M2842 should audit this design before any architecture or training design
continues. It should accept or reject:

```text
selected route:
  Route A driver-like recurrent-belief architecture/training redesign design

fallback route:
  limited-baseline freeze with explicit known failure taxonomy if redesign is
  judged too broad or not evidence-changing

blocked routes:
  same-surface M2838-like execution, direct Route C/HF3 retry without source,
  direct Route B paper/self-ID claim without a fair matrix
```

M2842 must preserve:

```text
M2838 weak diagnostic accounting: 1 success, 2 collisions, 13 off_track
actor observation shape 72 and action shape 3
no hidden/oracle actor input
prior-surface protected rows outside ordinary denominators
M2638/M2836 Route C/HF3 source dependency stop
no validation, ranking, promotion, performance, paper, current-sim,
high-fidelity, full-driver, or self-ID claim
```

## Rejected Claims

M2841 rejects:

```text
repair_success
recoverability_success
validation_readiness
validation_result
driver_performance
controller_family_ranking
source_family_ranking
task_family_ranking
profile_ranking
stress_axis_ranking
scenario_role_ranking
winner_selection
checkpoint_promotion
success_rate_verdict
paper_evidence
finite_window_vs_gru_conclusion
current_sim_verdict
high_fidelity_validation_readiness
high_fidelity_validation_result
full_ideal_driver_completion
level3_self_identification
```

## Next

Route to:

```text
m2842-engineering-controller-route-a-post-hf3-stop-negative-evidence-architecture-redesign-or-freeze-result-audit
```

If M2842 accepts this design, the next branch should pre-register a concrete
architecture/training redesign protocol. If M2842 rejects it, the branch should
fall back to explicit limited-baseline freeze or stop rather than repeating
M2838-like diagnostic execution.
