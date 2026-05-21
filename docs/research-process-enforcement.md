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
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift pytest -q tests/test_research_validate.py
```

Results:

```text
research validation passed (enforce_from_priority=870, enforced_tasks=1)
5 passed
```

The full test suite should also be run before commit.
