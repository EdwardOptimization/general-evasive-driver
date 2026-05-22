# M191 Stage3 Broader Evaluation

M190 showed that stage3 repeats preserve all existing gates, but the fixed M183
objective plateaus around M189. M191 therefore does not train. It evaluates the
current best M189 checkpoint on fresh behavior seeds and repeats the existing
proof-surface guards before any stage4 decision.

Current best under test:

```text
runs/ppo_m189_stage3_from_m188_seed5193/checkpoint.pt
```

## Behavior Seeds

M191 runs seeds `9505` and `9506`, beyond the previous `9503`/`9504` retention
pair.

Artifacts:

- `runs/m191_behavior_gate_seed9505`
- `runs/m191_behavior_gate_seed9506`

Seed `9505`:

| Policy | Success | Collision | Mean margin |
| --- | ---: | ---: | ---: |
| m184_s20 | 0.8625 | 0.1375 | 1.837808 |
| m188_5191 | 0.8625 | 0.1375 | 1.838104 |
| m189_5193 | 0.8625 | 0.1375 | 1.838230 |
| m189_5193_noact | 0.8625 | 0.1375 | 1.840872 |
| m189_5193_reset | 0.8500 | 0.1250 | 1.835853 |
| m189_5193_zero_all | 0.8000 | 0.1250 | 1.853439 |

Seed `9506`:

| Policy | Success | Collision | Mean margin |
| --- | ---: | ---: | ---: |
| m184_s20 | 0.8625 | 0.1375 | 1.855583 |
| m188_5191 | 0.8625 | 0.1375 | 1.855874 |
| m189_5193 | 0.8625 | 0.1375 | 1.855994 |
| m189_5193_noact | 0.8625 | 0.1375 | 1.857831 |
| m189_5193_reset | 0.8500 | 0.1250 | 1.852174 |
| m189_5193_zero_all | 0.8000 | 0.1250 | 1.871529 |

M189 keeps the same `0.8625` success rate as M184 and M188 on both fresh seeds.
Reset-hidden still degrades success to `0.85`, and zero-all-response still
degrades success to `0.80`. No-action-history remains behavior-neutral on this
coarse success metric.

## Boundary Replay

Artifacts:

- `runs/m191_m168_boundary_replay_gate_seed9510`
- `runs/m191_m170_boundary_replay_gate_seed9510`

| Candidate | Corpus | Rows | Baseline drops | Candidate drops | Normal margin delta | Margin gap delta | Gate pass |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| m189_5193 | M168 strict | 16 | 16 | 16 | +0.000677 | +0.000331 | true |
| m189_5193 | M170 split | 17 | 17 | 17 | -0.000689 | +0.000154 | true |

The current best checkpoint preserves every M168 and M170 boundary replay
success-drop row.

## Protected Key

Artifact:

```text
runs/m191_critical_key_seed9944
```

| Policy | Accepted cases | Pass | Margin gap |
| --- | ---: | --- | ---: |
| m184_s20 | 1 / 1 | true | 0.008957 |
| m189_5193 | 1 / 1 | true | 0.034931 |

Protected key `9944|perturbed|28|28` passes for M189. As in earlier positive
runs, `guard_validated=false` only means no non-reference policy failed in this
two-policy replay; the per-policy protected-case pass is the retention signal.

## Decision

M191 is positive as a broader retention gate:

- M189 keeps behavior success on two fresh seeds;
- reset and zero-all response ablations still reduce success;
- M168 and M170 boundary replay surfaces are retained;
- the protected key is retained, with a larger M189 margin gap than M184.

This does not yet justify longer PPO. The fixed objective has plateaued and the
proof-surface evidence is still mostly inherited from M183. The next step should
refresh the current-best proof surface before any stage4 continuation.

Decision:

```text
broaden_proof_surface_before_stage4
```
