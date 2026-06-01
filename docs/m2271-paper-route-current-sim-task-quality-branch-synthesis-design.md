# M2271 Paper-Route Current-Sim Task-Quality Branch Synthesis Design

- status: completed
- decision: `current_sim_task_quality_synthesis_design_admit_m2272`
- manifest: `experiments/manifests/m2271-paper-route-current-sim-task-quality-branch-synthesis-design.json`
- follow-up synthesis artifact: `docs/m2272-paper-route-current-sim-task-quality-branch-synthesis.md`

## Purpose

M2271 freezes the scope for a branch-level synthesis after M2270 stopped the
immediate scalar reward-repair loop. This is a design milestone only. It does
not run reset, rollout, measured execution, training, replay, PPO, private
holdout, ranking, or promotion.

The synthesis must answer:

```text
Did current-sim task-quality evidence improve enough to continue repair?
Or is the current blocker broader task/scenario quality rather than another
road-margin/offtrack reward scalar?
```

## Governing Plans

M2271 read and follows:

```text
docs/self-id-go-no-go-paper-route-plan.md
docs/paper-route-finite-window-vs-gru-plan.md
```

Implications:

- self-ID and GRU belief remain bounded hypotheses, not assumed truths;
- current-response or finite-window controllers may be the correct engineering
  answer;
- source-singleton or public diagnostic rows cannot support paper-level
  mechanism claims;
- current-sim task quality must be fixed before controller-family ranking;
- high-fidelity validation remains downstream of the current-sim verdict.

## Evidence Window

M2272 should synthesize these evidence blocks:

```text
M2236:
  matched-budget training branch synthesis; readiness floor failed.

M2238-M2239:
  task/curriculum readiness diagnosis; route to training stability and task
  curriculum repair.

M2241-M2244:
  same-budget checkpoint selection and outcome localization; offtrack-dominated
  failure identified.

M2250-M2257:
  generic offtrack/recovery/corridor repair; return improved but offtrack
  worsened, localized to midcourse/mild boundary regression.

M2258-M2270:
  targeted midcourse containment repair; slice recovery supported, but global
  offtrack remains neutral versus M2244 and profile readiness remains unproven.
```

## Required Questions

M2272 must answer the standard synthesis questions:

```text
evidence_summary
supported_claims
falsified_claims
failure_taxonomy_summary
public_gate_overfit_risk
next_branch_decision
```

It must also explicitly classify each branch result under the paper-route axes:

```text
engineering driver performance
mechanism evidence for history dependence
scenario/task-quality evidence
high-fidelity validation readiness
workflow or complexity reduction
```

## Decision Options

M2272 may choose only one of:

```text
continue:
  current-sim task-quality branch continues, but only with a new evidence axis
  such as scenario distribution quality or task-family construction.

pivot:
  stop reward-scalar local repair and pivot to scenario/task-quality redesign,
  benchmark-pack construction, or role-specific metric repair.

stop:
  current-sim task-quality branch lacks actionable evidence; do not continue
  without user review.

promote_to_next_branch:
  targeted containment evidence is sufficient to close this branch and start a
  new named branch with explicit paper-route scope.
```

## Blocked Shortcuts

M2272 must not:

```text
run training or measured execution
rank controller families
select a winner
claim finite-window-vs-GRU verdict
claim level3 self-identification
claim paper-level result
recommend another scalar reward tweak without a new evidence axis
```

## M2272 Registration

M2272 should be:

```text
m2272-paper-route-current-sim-task-quality-branch-synthesis
```

Required artifact:

```text
docs/m2272-paper-route-current-sim-task-quality-branch-synthesis.md
```

The expected decision is not pre-committed. The synthesis should decide from
the evidence whether the next branch is scenario/task quality, controlled
comparison redesign, or a stop/pivot.
