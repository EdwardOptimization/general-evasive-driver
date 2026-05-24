# Research Process Enforcement

This note records the repository-level process guard added after M89. The goal
is to make the research workflow enforceable by local tooling, rather than
depending only on narrative docs.

## Scope

The validator is intentionally lightweight. It checks repository state and
metadata, not training quality. Long-running training, benchmark promotion, and
driver gates remain explicit experiment commands.

The enforcement starts at priority `870`, which corresponds to:

```text
m90-guarded-ppo-from-wheel-objective-checkpoint
```

Historical M8-M89 tasks remain valid legacy records. New M90+ tasks must satisfy
the stricter process.

## Added Files

```text
src/autodrift/research_validate.py
tests/test_research_validate.py
experiments/scoreboard.csv
experiments/manifests/m90-guarded-ppo-from-wheel-objective-checkpoint.json
```

The tracked pre-commit template now runs the validator:

```text
scripts/hooks/pre-commit
```

The currently installed local hook was updated as well:

```text
.git/hooks/pre-commit
```

## Validator

Run:

```bash
make research-validate
```

or:

```bash
PYTHONPATH=src python -m autodrift.research_validate
```

The validator checks:

- `experiments/research_queue.csv` parses and has valid statuses;
- `experiments/research_status.json` counts match the queue;
- `next_task` matches the next planned or pending queue entry;
- `last_result` references an existing task and existing run/doc artifacts when
  paths are present;
- `experiments/scoreboard.csv` has the exact scoreboard schema;
- each enforced task has a manifest in `experiments/manifests`;
- completed enforced tasks have a scoreboard row;
- completed enforced tasks have all manifest-declared required artifacts.
- completed enforced tasks with structured `metric_extractors` and `gates`
  have a scoreboard decision matching the recomputed gate result.

## Manifest Runner

M90+ manifests can now be executed as the source of truth:

```bash
make research-manifest-run
```

or:

```bash
PYTHONPATH=src python -m autodrift.research_manifest run \
  --manifest experiments/manifests/m90-guarded-ppo-from-wheel-objective-checkpoint.json \
  --scoreboard experiments/scoreboard.csv
```

The runner executes the manifest `commands` in order, writes per-command logs,
and emits:

```text
runs/research_manifest/<manifest-id>_<timestamp>/run_receipt.json
```

The receipt records:

- manifest id;
- git commit and dirty status;
- Python/platform metadata;
- command return codes and log paths;
- required artifact existence, size, and sha256 hash.

For heavyweight experiments that are run manually, the metrics can still be
closed into the same harness afterwards:

```bash
make research-manifest-summarize
```

This extracts manifest-declared metrics, evaluates structured gates, and
upserts the task row in `experiments/scoreboard.csv`.

## Manifest Schema

Every enforced task must have:

```text
id
type
hypothesis
success_criteria
failure_criteria
commands
required_artifacts
baseline_checkpoints
decision_rule
```

Allowed manifest types:

```text
infrastructure
objective_sanity
driver_candidate
gate
```

The M90 manifest pre-registers:

- training command;
- ablation gate command;
- relevance audit command;
- success and failure criteria;
- required artifacts;
- baseline checkpoints;
- decision rule.

M90 also defines structured fields:

```text
metric_extractors
gates
decision_labels
scoreboard_checkpoint
```

`metric_extractors` read named values from CSV artifacts. `gates` compare those
values against preregistered thresholds, including metric differences such as:

```text
success_rate - zero_wheel_success >= 0.10
```

The scoreboard decision is generated from these gates instead of hand-written
after the result is known.

## Scoreboard

Added:

```text
experiments/scoreboard.csv
```

Fields:

```text
milestone,type,checkpoint,success_rate,termination_rate,
clearance_margin_mean,reset_success,zero_wheel_success,
zero_all_success,wheel_gain_mu,decision,reason
```

The first row is M89, because it is the current wheel-aware warm-start
candidate. Completed enforced tasks from M90 onward must add a row.

## Pre-Commit

The hook now runs:

```bash
PYTHONPATH="${PYTHONPATH:-src}" "${PYTHON:-python}" -m autodrift.research_validate
```

This happens before the existing lightweight harness tests. It does not run
training or benchmarks.

To install the tracked hook template:

```bash
make hooks-install
```

## Validation

Commands run after implementation:

```bash
make research-validate
python -m compileall -q src tests
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift pytest -q tests/test_research_manifest.py tests/test_research_validate.py tests/test_research_cycle.py
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift pytest -q
scripts/hooks/pre-commit
```

Results:

```text
research validation passed (enforce_from_priority=870, enforced_tasks=1)
13 passed for the focused research harness tests
247 passed for the full suite
16 passed from the pre-commit lightweight path
```

## Process V2

The M227 workflow upgrade adds a second enforcement layer. It starts at
priority `2220`:

```text
m227-ppo-smoke-retention-failure-audit
```

M90-M226 remain under the original manifest rules. M227+ manifests must also
declare evidence-governance fields:

```text
gate_tier
promotion_decision
failure_types
lineage
review_artifact
public_gates
private_holdout_policy
forbidden_shortcuts
```

The validator accepts these gate tiers:

```text
proof
generalization
promotion
process
infrastructure
```

Failure classification is required for rejected or repair-path completed
milestones. The taxonomy is intentionally short:

```text
proof_washout
objective_overfit
behavior_regression
seed_fragility
lineage_invalid
contract_violation
metric_artifact
training_instability
protected_key_window_failure
promotion_gate_failure
private_holdout_contamination
none
```

Lineage is now explicit:

```text
parent_checkpoint
parent_dataset
parent_config
parent_objective
derived_from
blocked_by
supersedes
invalidates
```

The goal is to prevent the research loop from becoming only a fixed-gate
passing machine. Public gates are allowed for daily debugging and repair.
Private holdout policy must be declared separately; private holdouts are for
promotion or paper evidence, not routine repair. If a private holdout result is
used to repair a candidate, the holdout must be rotated before being treated as
unbiased evidence again.

## Process V3: Workflow Synthesis

The M690 workflow upgrade adds branch-synthesis enforcement. It starts at
priority `6850`:

```text
m690-gate-margin-response-amplification-audit
```

M690+ manifests must declare:

```text
workflow_synthesis.branch
workflow_synthesis.evidence_axis
workflow_synthesis.claim_scope
workflow_synthesis.stop_condition
workflow_synthesis.fallback_plan
workflow_synthesis.synthesis_cadence
workflow_synthesis.synthesis_trigger
```

`stop_condition` and `fallback_plan` are non-empty lists. `synthesis_cadence`
must be an integer from 10 to 20. The validator rejects new M690+ manifests
that omit this section, so the pre-commit hook blocks narrow "just keep going"
research loops that do not declare branch stop, fallback, and synthesis rules.

The purpose is to force every branch to state:

- what evidence axis it is advancing;
- what claim scope is allowed;
- when to stop local iteration;
- what fallback path should be tried if the branch fails;
- when to synthesize the branch instead of adding another narrow milestone.

This implements the workflow-synthesis rule as repository state, not a
prompt-only preference.

## Review Generator

M227 also adds a deterministic review artifact generator:

```bash
make research-review RESEARCH_MANIFEST=experiments/manifests/m227-ppo-smoke-retention-failure-audit.json
```

or:

```bash
PYTHONPATH=src python -m autodrift.research_review \
  --manifest experiments/manifests/m227-ppo-smoke-retention-failure-audit.json \
  --scoreboard experiments/scoreboard.csv
```

It writes:

```text
docs/reviews/<manifest-id>.md
experiments/reviews/<manifest-id>.json
```

The review captures hypothesis, lineage, public gates, holdout policy,
forbidden shortcuts, failure taxonomy, scoreboard decision, and next blocker.
Completed M227+ tasks must have the declared `review_artifact` on disk.

## Hook Boundary

The pre-commit hook remains intentionally cheap. It runs:

```text
git diff --cached --check
python -m autodrift.research_validate
lightweight tests unless AUTODRIFT_SKIP_PRECOMMIT_TESTS=1
```

It does not run long PPO, private holdouts, scenario-distribution evaluations,
or promotion gates. Those belong in manifest commands and milestone review,
not in the commit hook.

## Agent Skill

The local Codex skill is:

```text
/home/quyaonan/.agents/skills/autodrift-research-harness/SKILL.md
```

Its job is behavioral, not authoritative. It tells future agent sessions to read
the live queue/status/manifest first, preserve the human-view input contract,
use process-v2 lineage and failure taxonomy, generate review artifacts, and run
the repository validator. The authoritative enforcement remains in
`autodrift.research_validate` and the pre-commit hook.
