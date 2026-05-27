# Self-Identification Evidence Discipline

This document turns the current self-identification review lessons into a
repo-owned research rule. It is not a milestone result and it does not change
the actor input contract. It defines what future manifests must state before
they make any claim about online hidden-dynamics self-identification.

## Why This Rule Exists

The project goal is a deployable, human-view RL driver that forms useful
implicit belief about hidden vehicle capability from its own commands and
vehicle response history. That claim is stronger than robust closed-loop
driving.

The main risk is current-frame substitution. The canonical human-view frame
contains ego response and actuator state, and those signals can be enough for a
policy to reactively adapt without encoding a durable history-based belief. If
the current frame dominates behavior, a policy can pass broad driving tasks
while still failing to prove history-based self-identification.

This rule prevents the research loop from converting ordinary robustness into a
self-identification claim.

## Claim Levels

Use the weakest supported level in every manifest and milestone.

`not_applicable`
: The milestone is infrastructure, process, corpus export, documentation, or
  another task that makes no driver capability or self-identification claim.

`level0_no_adaptation`
: The result only shows fixed or near-fixed behavior under hidden-condition
  changes. It does not show useful closed-loop adaptation.

`level1_closed_loop_reactive`
: The policy adapts through current observation feedback, but history
  interventions are not shown to be necessary for the outcome.

`level2_history_encoded_reactive`
: Recurrent/action-response history measurably changes actions, margins, or
  outcomes under reset, zero-response, delayed-history, zero-action-history, or
  wrong-matched-history interventions.

`level3_anticipatory_self_identification`
: The policy uses pre-emergency or warm-up command-response evidence before the
  critical maneuver. Current-frame evidence alone is intentionally insufficient
  or delayed/noisy, and history interventions damage the anticipatory decision.

## Required Manifest Field

From M1090 / priority 10850 onward, every research manifest must include:

```json
"self_id_evidence_discipline": {
  "claim_level": "not_applicable",
  "current_frame_substitution_risk": "State how current ego/scene frame evidence could replace history.",
  "history_necessity_tests": [
    "normal vs reset-hidden",
    "normal vs zero-current-response",
    "normal vs zero-action-history",
    "normal vs delayed-history",
    "normal vs wrong-matched-history"
  ],
  "temporal_evidence_window": "State whether the task gives only current-frame evidence or a warm-up/pre-emergency evidence window.",
  "negative_result_policy": "State how null or weak history-intervention results will be recorded and routed.",
  "allowed_claims": [
    "The scoped claims this milestone is allowed to make."
  ]
}
```

The validator checks field presence and the allowed `claim_level` vocabulary.
The scientific burden remains with the milestone: higher claim levels need
actual gates, not just text.

## Interpretation Rules

Do not equate high success rate with self-identification. High success can be a
valid capability result while only supporting `level1_closed_loop_reactive`.

Do not treat a null hidden-swap or reset-hidden result as proof that the policy
is useless. It may mean the task gives enough current-frame information, the
history evidence window is too short, or the intervention does not touch the
behaviorally relevant latent.

Do not promote a self-identification claim from a public proof row alone. The
claim needs source-diverse proof rows, fresh scenarios, and history-necessity
interventions that affect margins, actions, or outcomes.

Use negative results as task-design evidence. If history interventions do not
matter, route to better temporal evidence windows, delayed/noisy current
response, anticipatory tasks, or stricter matched-current-state scenarios
instead of weakening the proof standard.

## Design Implications

For level 2 evidence, prefer scenarios where current scene geometry is matched
but injected history differs, so the intervention tests command-response belief
instead of route or obstacle geometry.

For level 3 evidence, prefer tasks with a preparation phase before the obstacle
or critical maneuver. The policy should have time to observe its own actuator
commands and vehicle response before the decision point.

For delayed/noisy observation experiments, document whether degraded current
response is part of the actor input contract, an evaluation intervention, or a
new task family. Do not mix these interpretations in one claim.

For paper-quality claims, report the supported claim level explicitly. A
methodology or negative-result paper can still be valid if it honestly shows
that robust closed-loop RL is easier than proving anticipatory self-ID.
