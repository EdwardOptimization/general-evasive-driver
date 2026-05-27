# M1087 Staged Training Discipline Harness Rule

## Purpose

M1087 turns the pretrain -> posttrain -> guarded RL concept into a durable repo
document and a validator-enforced harness rule.

This milestone does not train, run PPO, promote, use private holdout, or run
new mining.

## Why This Rule Exists

The current research history repeatedly shows that PPO should not be treated as
the first training method. Before proof and action-grounding stabilize, PPO can
wash out self-ID evidence or make wrong-history branches safe.

The staged interpretation is:

```text
behavior_pretrain:
  learn basic closed-loop driving and action priors.

capability_pretrain:
  make recurrent state encode future response/capability envelope.

action_grounding_posttrain:
  connect capability/history signal to steer/throttle/brake corrections under
  exact/proof/active-set gates.

guarded_rl:
  use PPO only as a small proposal step after pre/posttrain and proof-retention
  evidence exist.
```

## Durable Artifacts

New durable rule document:

```text
docs/training-stage-discipline.md
```

Updated harness code:

```text
src/autodrift/research_schema.py
src/autodrift/research_validate.py
tests/test_research_validate.py
```

## Validator Rule

Process-v4 starts at priority:

```text
10820
```

Every future manifest at or above that priority must declare:

```text
training_stage.stage
training_stage.stage_objective
training_stage.admission_evidence
training_stage.blocked_shortcuts
training_stage.allowed_updates
training_stage.next_stage_criteria
```

Allowed stages:

```text
process
infrastructure
evaluation_only
behavior_pretrain
capability_pretrain
action_grounding_posttrain
guarded_rl
```

The validator rejects `autodrift.train_ppo` commands unless the manifest uses:

```text
training_stage.stage: guarded_rl
```

For `guarded_rl`, the manifest must also cite:

```text
pre/posttrain capability evidence;
exact/proof/public-gate evidence;
rollback, retention, repair, or projection protection.
```

## M1088 Preservation

The previously planned existing-artifact smoke is not dropped. It is shifted to:

```text
m1088-v4-public-base-source-balanced-boundary-existing-artifact-smoke
```

M1088 is marked as infrastructure stage, not guarded RL.

## Decision

```text
staged_training_discipline_harness_rule_admit_m1088_existing_artifact_smoke
```

Next:

```text
m1088-v4-public-base-source-balanced-boundary-existing-artifact-smoke
```
