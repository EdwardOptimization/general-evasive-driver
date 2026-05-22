# M207 Stage6 Protected-Key Failure Audit

M207 audits why M206 failed the protected key before any further PPO
continuation.

No PPO or actor update is run in this milestone.

## Inputs

Primary artifacts:

- `runs/m206_critical_key_seed9944/guard_results.csv`
- `runs/m206_critical_key_seed9944/m206_stage6_candidates.csv`
- `runs/m206_fixed_batch_outcome_eval_seed37/summary.json`
- `runs/m206_behavior_gate_seed9505/policy_summary.csv`
- `runs/m206_behavior_gate_seed9506/policy_summary.csv`

Reference protected-key manifest:

```text
runs/m133_zero_relvel_s60_strict_60ep_seed9900/manifest.json
```

Relevant reference thresholds:

| Field | Value |
| --- | ---: |
| min_margin_gap | 0.005 |
| min_normal_margin | 0.0 |
| max_normal_margin | 0.2 |
| require_normal_success | true |

## Protected Key Result

Protected key:

```text
9944|perturbed|28|28
```

| Policy | Accepted cases | Normal success | Normal margin | Wrong-history margin | Margin gap |
| --- | ---: | --- | ---: | ---: | ---: |
| m199_5201 | 1 / 1 | true | 0.119416 | 0.068219 | 0.051197 |
| m204_stage5 | 1 / 1 | true | 0.189607 | 0.094102 | 0.095505 |
| m206_stage6 | 0 / 1 | true | 0.207450 | 0.109548 | 0.097903 |

M206 does not fail because broad behavior collapses:

- fixed M193 objective improves from M204 `0.158475` to M206 `0.158420`;
- smoke eval termination is `0.00`;
- behavior seeds `9505` and `9506` keep success `0.8625`;
- old M183 replay retains `16/16` and `17/17` success drops;
- refreshed M193 replay retains `14/14` success drops.

## Failure Mechanism

The protected-key row remains normally successful and still has a large
wrong-history margin gap. The failure mechanism is boundary-window excursion:

```text
M206 normal margin = 0.207450
reference max_normal_margin = 0.2
```

Because the pre-registered protected-key guard requires the selected key to
remain within the near-boundary acceptance window, M206 is rejected even though
its normal margin is larger.

This is intentional for the current proof surface: the key is useful as a
near-boundary self-ID diagnostic only while it remains in the boundary window.
Changing the threshold after seeing M206 would weaken the harness.

## Decision

Keep M204 as the current best retained checkpoint. Do not promote M206.

The next action is one fresh-seed stage6 retry from M204 with the same frozen
recipe. This is allowed because M206's failure looks seed/update-specific and
not a broad behavior or replay collapse.

If that retry also fails the protected key, stop repeating the same PPO recipe
and design a protected-key-aware objective/config change before further PPO.

Decision:

```text
admit_one_stage6_retry_from_m204
```

Next step:

```text
m208-stage6-protected-key-retry-from-m204
```
