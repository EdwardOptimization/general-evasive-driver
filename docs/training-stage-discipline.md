# Training Stage Discipline

This document makes the project training flow explicit and enforceable. The
driver is not trained by treating PPO as the first or primary optimizer. The
project uses a staged sequence:

```text
behavior pretrain
  -> capability pretrain
  -> action-grounding posttrain
  -> guarded RL
```

The stages are not marketing labels. They are admission rules for manifests,
reviews, and future promotion decisions.

## Stage Meanings

### Behavior Pretrain

Goal:

```text
learn basic closed-loop evasive driving and actuator-level action priors.
```

Typical evidence:

```text
L2 teacher to L3 online-GRU behavior cloning
route and obstacle behavior retention
clean P0 human-view input contract
```

This stage can show the actor can drive. It does not prove recurrent belief or
history causality.

### Capability Pretrain

Goal:

```text
make recurrent state encode future controllability and response envelope.
```

Typical evidence:

```text
future braking/yaw/lateral response prediction
matched-current capability contrast
active diagnostic history
hidden-state probes
```

This stage should avoid treating `mu` prediction as the main target. The useful
target is capability envelope: what braking, yaw, lateral authority, delay, or
recovery margin the current vehicle-road system can deliver.

### Action-Grounding Posttrain

Goal:

```text
connect capability/history signal to steer/throttle/brake corrections.
```

Typical evidence:

```text
direction-family targets
temporal sequence objectives
residual heads
actor_mean or fusion adapters
combined active-set anchors
exact no-regression gates
public proof replay gates
```

This stage is where hidden/capability signal becomes action. It is still not a
license to promote broad claims unless proof, behavior, and generalization
gates agree.

### Guarded RL

Goal:

```text
use PPO only as a small closed-loop proposal step after the prior stages have
made the policy capable and proof-retained.
```

Guarded RL admission requires all of:

```text
1. behavior or capability pretrain evidence;
2. action-grounding posttrain evidence;
3. exact/proof gate evidence;
4. rollback, repair, projection, or retention protections;
5. no actor-input contract change;
6. explicit failure taxonomy and rejection rule.
```

PPO is treated as a noisy proposal generator. Acceptance is controlled by exact
objectives, proof replay, source-diverse diagnostics, fresh/OOD behavior gates,
and hard rollback rows.

## Process-V4 Manifest Rule

From priority `10820` onward, every manifest must include:

```json
"training_stage": {
  "stage": "infrastructure",
  "stage_objective": "...",
  "admission_evidence": ["..."],
  "blocked_shortcuts": ["..."],
  "allowed_updates": ["..."],
  "next_stage_criteria": ["..."]
}
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

The harness rejects a manifest that runs `autodrift.train_ppo` unless
`training_stage.stage == "guarded_rl"`.

For `guarded_rl`, the admission evidence must cite:

```text
pretrain or posttrain/capability/action-grounding evidence;
exact/proof/public-gate evidence;
rollback, retention, repair, or projection protection.
```

This is intentionally stricter than documentation. It prevents future research
from accidentally treating PPO as an early-stage optimizer.

## Non-Goals

This rule does not claim the driver is complete.

It does not promote a checkpoint.

It does not replace proof, generalization, behavior, or private-holdout
discipline.

It only ensures each milestone says which stage it belongs to and prevents PPO
from bypassing the staged admission chain.
