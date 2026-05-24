# M606 Grounded Capability-Action Target Miner Implementation

## Purpose

M606 implements and runs the simulator-grounded target miner designed by M605.

Question:

```text
Can M604 belief-only capability-action gaps be converted into local first-action
targets that improve short-horizon simulator margin or risk?
```

Scope:

```text
no training
no PPO
no checkpoint promotion
no privileged actor input
no direct use of belief-only gaps as action labels
```

## Implementation

Added:

```text
src/autodrift/grounded_capability_action_target_miner.py
tests/test_grounded_capability_action_target_miner.py
```

The miner:

1. reads M604 `candidate_for_grounding` rows;
2. keeps reconstructable real-history variants:
   `wrong_matched_history` and `delayed_history`;
3. removes duplicate physical rows with the same surface / variant / target /
   left state / right state key;
4. reconstructs BC5660 rollout snapshots from the fresh and OOD configs;
5. evaluates a bounded first-action override grid around the actor base action;
6. continues rollout under the unchanged BC5660 policy;
7. accepts targets only when they improve simulator margin or risk inside the
   action trust region;
8. writes every candidate rollout plus accepted and unaccepted row artifacts.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.grounded_capability_action_target_miner \
  --checkpoint-policy bc5660=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --coupling-rows runs/m604_guarded_capability_action_coupling_evaluator/coupling_rows.csv \
  --surface-config fresh=configs/ppo_m541_matched_l3_variance_4096.json \
  --surface-config ood=configs/eval_m574_moderate_ood_l3.json \
  --include-variant wrong_matched_history \
  --include-variant delayed_history \
  --max-rows-per-surface-variant-target 4 \
  --max-total-rows 32 \
  --steer-deltas=-0.08,-0.04,-0.02,0,0.02,0.04,0.08 \
  --throttle-deltas=-0.06,-0.03,0,0.03 \
  --brake-deltas=-0.08,-0.04,-0.02,0,0.02,0.04,0.08 \
  --min-margin-improvement 0.02 \
  --min-risk-improvement 0.05 \
  --max-action-l2 0.10 \
  --max-continuation-steps 40 \
  --device cpu \
  --run-dir runs/m606_grounded_capability_action_target_miner
```

## Artifacts

```text
runs/m606_grounded_capability_action_target_miner/summary.json
runs/m606_grounded_capability_action_target_miner/selected_source_rows.csv
runs/m606_grounded_capability_action_target_miner/target_candidates.csv
runs/m606_grounded_capability_action_target_miner/accepted_targets.csv
runs/m606_grounded_capability_action_target_miner/unaccepted_rows.csv
```

No `target_corpus.npz` was written because there were no accepted targets.

## Results

The bounded smoke selected `23` unique source rows and evaluated `4508`
candidate first-action rollouts.

Summary:

| Metric | Value |
| --- | ---: |
| selected source rows | `23` |
| candidate rollouts | `4508` |
| trust-region candidate rollouts | `3696` |
| accepted targets | `0` |
| unaccepted rows | `23` |
| max candidate margin improvement | `0.014268` |
| max trust-region margin improvement | `0.013046` |
| max candidate risk improvement | `0.014268` |
| max trust-region risk improvement | `0.013046` |

Candidate rejection counts:

| Reason | Count |
| --- | ---: |
| insufficient margin or risk improvement | `3214` |
| outside action trust region | `812` |
| candidate collision | `482` |

The best unaccepted row improved margin by only `0.014268`, and that candidate
was outside the configured `0.10` action-L2 trust region. Inside the trust
region, the best margin/risk improvement was `0.013046`, below the M605
acceptance threshold of `0.02`.

## Interpretation

M606 is a useful negative grounding result.

It shows that the initial local first-action grid does not find simulator-
grounded targets strong enough to justify actor training from M604 belief-only
gaps. Therefore M604 rows still must not be used as action labels.

This does not falsify the capability-action coupling direction. It narrows the
next question:

```text
Are these rows too far from a short-horizon safety boundary, is the first-action
grid too local, or is the belief-only movement not behaviorally actionable under
BC5660?
```

## Contract Checks

```text
labels_enter_actor_input: false
actor_parameters_changed: false
ppo_used: false
promoted: false
```

The miner uses simulator labels only as offline target-screening artifacts. No
labels, hidden parameters, or target outputs enter the deployable actor input.

## Decision

Decision:

```text
grounded_capability_action_target_miner_negative_admit_audit
```

M606 passes as infrastructure because it writes the required artifacts and does
not train or promote anything. The target-mining hypothesis is not supported by
this first bounded grid because zero accepted targets were found.

Next:

```text
m607-grounded-target-mining-audit
```
