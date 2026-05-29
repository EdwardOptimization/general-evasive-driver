# M1426 Paper-Route Action-Divergent Pressure Result Audit

## Summary

M1426 audits the M1425 source-smoke result before any replay or training.

Decision:

```text
action_divergent_pressure_audit_admit_bounded_relocation_replay_design
```

M1426 does not run closed-loop replay, outcome interventions, train, run PPO,
promote, use private holdout, export a training corpus, or change actor inputs.

## What M1425 Proved

M1425 proved that the M1424 constructor can find source-diverse action-critical
rows:

```text
candidate_pool_rows: 625
candidate_rows: 256
candidate_unique_source_seeds: 12
candidate_unique_capability_pairs: 16
candidate_unique_reveal_buckets: 52
```

It also proved that bounded terminal-pressure proposals can be generated:

```text
outcome_pressure_rows: 846
outcome_pressure_unique_source_seeds: 7
outcome_pressure_unique_capability_pairs: 16
outcome_pressure_unique_reveal_buckets: 31
```

So this is not a source-materialization failure.

## What M1425 Falsified

M1425 falsifies the narrow claim that a shared-margin relocation proxy is enough
to create history-positive source rows from M1421:

```text
history_positive_rows: 0
candidate margin_gap max: 0.016403
candidate margin_gap p95: 0.003603
outcome_pressure margin_gap max: 0.002712
outcome_pressure margin_gap p95: 0.000535
pre-registered margin_gap threshold: 0.02
```

The action sequence changes are real, but the terminal-margin differences in
the original M1421 rollouts are almost zero or negative. A proxy that subtracts
the same obstacle pressure from normal and variant margins cannot turn those
rows into history-positive evidence.

## Failure Classification

Classification:

```text
scenario_sampling_failure
```

More specifically:

```text
source rows are action-divergent and diverse;
proxy pressure rows are diverse;
terminal-margin sensitivity is missing under shared-margin accounting.
```

This is not a contract violation, not PPO washout, not promotion failure, and
not a reason to lower the threshold after seeing the result.

## Why Bounded Relocation Replay Is Still Defensible

The shared-margin proxy is deliberately conservative and non-replay. It assumes
the relocation pressure affects normal and variant rollouts equally. Real
closed-loop replay under relocated obstacle geometry may break that equality:

```text
normal and history-variant actions may steer through different lateral traces;
small obstacle lateral/width changes can affect one trace but not the other;
variant actions can alter yaw/recovery timing before the obstacle zone;
the final terminal margin can become nonlinear in the action sequence.
```

Therefore M1425 blocks training and corpus export, but it does not block a
separately registered, bounded, no-training relocation replay design.

## Next Route

Admit a design-only milestone:

```text
m1427-paper-route-bounded-relocation-replay-design
```

M1427 should design a replay probe that:

```text
1. uses M1425 pressure rows as public candidate proposals;
2. reconstructs preferred and wrong warmup traces from the original config;
3. relocates the active obstacle only within the bounded M1425 offsets;
4. replays normal and history variants under the relocated scenario;
5. counts history-positive only when actual replay, not proxy, produces a
   success drop or margin gap >= 0.02;
6. reports reset/zero-current controls separately;
7. remains no-training and no-promotion.
```

The design must explicitly preserve the P0 actor input contract. Relocation is
a scenario-generation operation, not an actor input.

## Blocked Routes

Do not:

```text
lower the M1425 margin-gap threshold after seeing the result;
train from proxy rows;
export proxy rows as a training corpus;
run PPO;
promote any checkpoint;
claim self-identification from M1425;
skip directly into a large replay sweep without a design manifest.
```

## Guardrails

M1426 guardrail status:

```text
closed_loop_replay_started: false
outcome_interventions_started: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
training_corpus_exported: false
actor_input_contract_changed: false
level3_self_id_claim_made: false
```

## Conclusion

M1425 is a useful negative result, not a dead end. It shows the current branch
has action-divergent material and terminal-pressure proposals, but the proxy is
not enough to establish terminal-margin sensitivity. The next defensible step is
bounded relocation replay design, still no-training and no-promotion.
