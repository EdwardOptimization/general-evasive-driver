# Loop-state semantics during manual takeover (WP6.2 G3)

This document fixes the pause/ownership semantics for the three loop-state
files while the autonomous milestone loop is paused (takeover began
2026-06-11, `docs/feasibility-takeover-2026-06-route-decision.md`), and the
preconditions for resuming autonomy.

## Files covered

- `experiments/research_queue.csv`
- `experiments/research_status.json`
- `experiments/scoreboard.csv`

## State: PAUSED (current)

The autonomous loop does not select or execute tasks on its own. The three
files stay live but are written only through the takeover discipline:

| file | who may write | how |
|---|---|---|
| `research_queue.csv` | the human operator (PI/takeover agent) registering a milestone per the M3215+ playbook | append/edit rows with csv `lineterminator='\n'`; statuses limited to `planned/pending/running/completed/failed/blocked` |
| `research_status.json` | the harness only (`make research-plan`, `make research-run-next`) | never hand-edited; counts/next_task are recomputed |
| `scoreboard.csv` | the operator, one row per completed enforced milestone | exact `SCOREBOARD_FIELDS` header; decision/reason mirror the manifest decision rule |

Rules while paused:

1. Every queue mutation is followed by `make research-plan` (status refresh)
   and `make research-validate` (must be green in pending AND completed
   states of the milestone being registered).
2. Tasks are still EXECUTED through `make research-run-next` — manual
   bookkeeping of a "completed" row without a harness run dir is forbidden.
3. Long-running commands inside a milestone go through
   `scripts/run_managed.sh` (setsid + pidfile + log + exit-code file); the
   harness command may then be a short poller or the run is registered after
   the managed process finishes.
4. Historical rows (priority < 32200) are frozen evidence: never edited
   except to fix a validator-detected inconsistency, and never re-opened.
5. A blocked dependency produces an escalation file in `docs/escalations/`
   plus a `blocked` queue row — not a chain of bookkeeping completions
   (enforced by validator rule v7b).

## State: ARCHIVED (terminal alternative)

If the program ends without resuming autonomy, the three files become
read-only artifacts referenced by the papers; the only allowed change is a
header comment in `docs/current-status.md` declaring the archive date.

## Resuming autonomy (preconditions, all required)

The autonomous loop may resume only when all of the following hold:

1. **G1 feasibility-pricing gate live**: `make research-validate` enforces
   process v7 (priority >= 32200): repair/improvement/training milestones
   carry a `feasibility_pricing` block (pricing_artifact / priced_gap /
   threshold / gap_meets_threshold) and certified dead ends (the 7 residual
   rows seeds 401530/401541/401560/401631/401640/401641/401660, reflex-family
   drift_required repair, vehicle-spread reflex retuning) are auto-rejected
   without a new pricing artifact
   (`experiments/feasibility_audit/oracle_certification_results.json`,
   `experiments/feasibility_audit/c5_reflex_degradation.json`).
2. **G2 escalation hook live**: validator rule v7b fails consecutive
   dependency-unavailable completions without a `docs/escalations/` note
   (protocol: `docs/escalations/README.md`).
3. **G3 managed-runner live**: `scripts/run_managed.sh` exists and is the
   only sanctioned launcher for long measurements.
4. **Guardrail smoke passed**: the M3220 smoke
   (`scripts/wp62_guardrail_smoke.py` ->
   `experiments/wp62_guardrail_smoke.json`, `all_pass: true`) ran through the
   harness, demonstrating red (fake dead-end manifest rejected; missing
   escalation rejected) and green (compliant manifest passes; managed runner
   produces pid/log/exit_code) on the real validator code.
5. **Operator sign-off**: the PI flips the pause line in
   `docs/current-status.md` ("the autonomous loop is paused") to a dated
   resume entry. Until that edit exists, agents must treat the loop as
   paused regardless of guardrail state.

On resume, the loop inherits the takeover-era constraints that are not
validator-enforced: incumbent `ActiveSafetyReflexDriver` (v4) untouched,
pre-registration before every run, disjoint seed streams, and managed
background processes for anything longer than a smoke.
