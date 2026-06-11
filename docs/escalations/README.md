# Escalations — blocked-dependency protocol (WP6.2 G2)

This directory is the single place where a blocked external dependency is
escalated. The banned alternative is the bookkeeping loop: registering more
milestones on the same branch that each "complete" by re-stating that the
dependency is unavailable. The validator enforces this (process v7b in
`src/autodrift/research_validate.py`): within one `workflow_synthesis.branch`,
**two or more consecutive completed tasks whose queue notes/hypothesis carry
dependency-unavailable semantics fail `make research-validate`** ("escalate
instead of bookkeeping") unless a matching escalation file exists here.

## Protocol

1. A task hits a dependency it cannot resolve itself (missing solver, missing
   PI decision, missing external artifact, missing hardware/licence).
2. Write `docs/escalations/<YYYY-MM-DD>-<slug>.md` using the template below.
   The file must name the blocked `workflow_synthesis.branch` and/or the
   blocked milestone id(s) — the validator matches on those strings.
3. Set the blocked queue row(s) in `experiments/research_queue.csv` to
   `status=blocked` (never keep "completing" follow-up bookkeeping rows).
4. Refresh `experiments/research_status.json` via `make research-plan` and run
   `make research-validate`.
5. When the dependency is resolved, record the resolution at the bottom of the
   escalation file, set the row back to `pending`, and resume.

## Template

```markdown
# Escalation: <short title>

- date: <YYYY-MM-DD>
- blocked branch: <workflow_synthesis.branch>
- blocked milestones: <m####-..., m####-...>

## What is blocked

<one paragraph: the exact dependency, the artifact/decision that is missing,
and what work cannot proceed without it>

## Resume condition

<the observable condition under which the queue row goes back to pending,
e.g. "PI adjudicates the v5 promotion packet" or "chrono solver X released">

## Who can unlock it

<the person/role/system that owns the dependency, and how they were notified>

## Resolution (filled in when unblocked)

- date:
- outcome:
```

## Trigger semantics (validator-matched phrases)

The v7b detector matches these substrings (case-insensitive) in queue
notes/hypothesis of completed tasks at priority >= 32200: see
`PROCESS_V7B_DEPENDENCY_UNAVAILABLE_TOKENS` in
`src/autodrift/research_schema.py` (e.g. "dependency unavailable",
"blocked dependency", "missing dependency", "waiting on dependency",
"upstream unavailable"). If a milestone genuinely completes useful work,
do not phrase its notes as a dependency complaint; if it did not complete
useful work because of a dependency, escalate here instead of completing it.
