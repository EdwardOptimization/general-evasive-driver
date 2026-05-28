# M1194 Paper-Route Finite-Window vs GRU Infrastructure Synthesis

## Summary

M1194 synthesizes the M1184-M1193 paper-route infrastructure branch. This is a
process milestone required by the workflow synthesis cadence. It does not train
controllers, run PPO, run candidate replay, use private holdout, promote, or
change actor inputs.

Decision:

```text
continue
```

The branch should continue, but the next milestone must remain infrastructure:
integrate controller-profile observation masks into train/eval vector paths
before any L0/L1/L2/L3 training smoke.

## evidence_summary

The branch advanced from gate governance to executable controller-profile
infrastructure:

```text
M1184: designed gate utility audit
M1185: built gate utility matrix from existing artifacts
M1186: defined active gate policy
M1187: designed L0/L1/L2/L3 controller comparison
M1188: implemented controller profile scaffold
M1189: designed generated config production
M1190: generated eight smoke configs
M1191: implemented runtime observation-mask wrapper
M1192: ran no-training integrated profile runtime smoke
M1193: designed training smoke and identified train/eval mask integration gap
```

The current profile set is executable at single-env runtime-smoke level:

```text
L0_current_masked
L1_one_step
L2_window_13
L2_window_25
L2_window_50
L2_window_100
L3_online_gru
L3_reset_control
```

M1192 result:

```text
config_count: 8
all_configs_instantiated: true
l0_mask_observed: true
unmasked_profiles_unchanged: true
contract_ok: true
model_forward_ok: true
training_started: false
ppo_used: false
```

M1193 found the remaining blocker:

```text
train_ppo -> make_vector_env -> SyncAutoDriftVectorEnv / ParallelAutoDriftVectorEnv
vector envs construct AutoDriftEnv directly
controller_profile_runtime wrapper is not yet applied there
```

Therefore L0 training would currently leak previous-command fields in vector
training paths. Training remains blocked until train/eval integration is added.

## supported_claims

Supported claims:

```text
1. The paper route is now governed by an active gate policy rather than by all historical gates as unconditional blockers.
2. The L0/L1/L2/L3 comparison contract is explicit and keeps the deployable no-hidden/no-oracle actor boundary.
3. Eight generated profile configs exist for the planned comparison matrix.
4. The generated configs instantiate with AutoDriftEnv and ActorCritic under no-training runtime smoke.
5. L0 runtime masking works in the single-env wrapper path: raw step previous-command sum 1.45 becomes 0.0 after wrapping.
6. Unmasked L1/L2/L3 profiles remain unchanged in runtime smoke.
7. A fair training-smoke protocol is defined, but it correctly blocks direct training until vector-path masks exist.
```

The branch supports infrastructure readiness for the next integration step. It
does not yet support training readiness.

## falsified_claims

Falsified or blocked claims:

```text
1. Runtime metadata alone is enough for L0 training.
   False: train_ppo vector envs do not yet apply controller-profile masks.

2. Passing unit tests and single-env smoke means generated configs are ready for PPO.
   False: vector reset/step observations need focused integration tests.

3. GRU should be assumed superior before finite-window baselines.
   Unsupported: no profile training or comparison has been run.

4. Runtime smoke can justify driver-performance claims.
   False: M1192 only proves instantiation and mask behavior.

5. This branch provides self-identification evidence.
   False: no history-necessity, wrong-history, delayed-history, or same-current/different-history tests were run.
```

## failure_taxonomy_summary

No experimental failure occurred in M1194. The branch synthesis classifies the
main issue as a blocked integration gap:

```text
contract_violation risk:
  L0 would leak previous-command fields if training starts before vector-path masking.

metric_artifact risk:
  treating runtime-smoke success as training-readiness would overstate evidence.

training_instability risk:
  not yet tested; training loop has not run for generated profiles.

private_holdout_contamination:
  not applicable; no private holdout was used.
```

M1193 prevented the contract risk from becoming an actual training result by
blocking direct PPO.

## public_gate_overfit_risk

Current risk is moderate but controlled.

The recent branch did not optimize a policy against public proof rows. It
mainly built infrastructure and process controls. Public-gate overfit risk is
therefore lower than in proof-row repair branches.

Remaining risks:

```text
1. The profile comparison may overfit to smoke configs if the same tiny smoke setup becomes the comparison evidence.
2. L0/L1/L2/L3 may later receive accidental unequal tuning if early smoke results are used to repair one profile without resetting the protocol.
3. Runtime-smoke success could be mistaken for training or performance evidence.
4. Active gate policy may hide legacy proof regressions if later promotion skips Stack C at table-freeze time.
```

Controls:

```text
1. Keep smoke as plumbing evidence only.
2. Require shared seeds, budgets, env distribution, reward, action contract, and eval count before comparison.
3. Use separate manifests for train/eval mask integration, training smoke, fair comparison pilot, and paper-quality eval.
4. Preserve Stack B as active public proof default and Stack C as extended regression for promotion/table-freeze.
```

## next_branch_decision

Decision:

```text
continue
```

Continue the `paper_route_finite_window_gru_evidence` branch, but only with the
next infrastructure blocker:

```text
m1195-paper-route-train-entrypoint-profile-mask-integration
```

M1195 should:

```text
integrate controller-profile observation masks into train/eval vector paths;
prove L0 vector reset/step observations zero previous-command fields [9,10,11];
prove unmasked profiles remain unchanged;
avoid controller training, PPO, replay, promotion, private holdout, and actor-input expansion.
```

Only after M1195 passes should Stage A training smoke be admitted:

```text
L0_current_masked
L1_one_step
L2_window_25
L3_online_gru
1024 steps, 2 envs, 1 seed, CPU, no performance claim
```

## Decision

```text
paper_route_infrastructure_synthesis_continue_to_train_entrypoint_mask_integration
```

M1194 resets the branch synthesis cadence and admits exactly the train/eval
profile-mask integration milestone next. It does not admit controller training.
