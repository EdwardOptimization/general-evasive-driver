# M946 V4 Public Base Controlled Fusion Candidate Replay Gate Implementation

## Purpose

M946 implements the M945 no-training replay/proof-retention gate for the
materialized M944 primary candidate:

```text
runs/m944_v4_public_base_controlled_fusion_candidate_compatibility/interpolation/checkpoints/alpha_0_0725.pt
```

The comparison base remains:

```text
runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
```

M946 does not train, run PPO, use private holdout, or promote.

## Command

```bash
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
python -m autodrift.public_base_controlled_fusion_candidate_replay_gate \
  --base-checkpoint runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --candidate-checkpoint runs/m944_v4_public_base_controlled_fusion_candidate_compatibility/interpolation/checkpoints/alpha_0_0725.pt \
  --run-dir runs/m946_v4_public_base_controlled_fusion_candidate_replay_gate \
  --device cpu
```

## Artifacts

- Summary: `runs/m946_v4_public_base_controlled_fusion_candidate_replay_gate/summary.json`
- Public replay summary: `runs/m946_v4_public_base_controlled_fusion_candidate_replay_gate/public_replay_gate_summary.csv`
- Behavior comparison: `runs/m946_v4_public_base_controlled_fusion_candidate_replay_gate/behavior_comparison.csv`
- Source-diverse diagnostic: `runs/m946_v4_public_base_controlled_fusion_candidate_replay_gate/source_diverse_protected_diagnostic/summary.json`
- Old-key diagnostic: `runs/m946_v4_public_base_controlled_fusion_candidate_replay_gate/old_key_neighborhood_diagnostic/summary.json`

## Result

M946 fails the proof gate:

```text
result_class: public_base_controlled_fusion_candidate_replay_gate_proof_washout
failure_types: proof_washout
six_public_replay_gates_pass: false
public_replay_gates_passed: 5 / 6
failed_public_replay_surfaces: m267_m264
behavior_pass: true
actor_inputs_changed: false
training_started: false
ppo_used: false
promoted: false
```

Five public replay surfaces pass:

```text
M183/M168: pass, success_drop_count 16 -> 16
M183/M170: pass, success_drop_count 17 -> 17
M193/M189: pass, success_drop_count 14 -> 14
M212/M204: pass, success_drop_count 17 -> 17
M223/M219: pass, success_drop_count 17 -> 17
```

The failed surface is:

```text
M267/M264: fail, success_drop_count 17 -> 13
```

The candidate keeps normal success on that surface, but wrong-history rollouts
become successful on four rows:

| row_id | pair | left_step | right_step | base wrong margin | candidate wrong margin |
| --- | --- | ---: | ---: | ---: | ---: |
| 6 | `9530:15:9550:18` | 15 | 18 | -0.000267 | 0.000576 |
| 13 | `9530:9:9550:9` | 9 | 9 | -0.001118 | 0.000377 |
| 15 | `9530:21:9550:21` | 21 | 21 | -0.000203 | 0.000556 |
| 16 | `9530:6:9550:6` | 6 | 6 | -0.000708 | 0.000934 |

This is not a behavior regression on the broad behavior seeds. It is a
mechanism proof regression: the candidate makes some rejected/wrong-history
branches safe.

## Diagnostics

Behavior seeds are retained:

```text
seed 9505: candidate success delta 0.0, ordering normal >= reset >= zero-all retained
seed 9506: candidate success delta 0.0, ordering normal >= reset >= zero-all retained
```

Source-diverse diagnostic is mixed:

```text
current_m333_surface: pass, success_drop_count 17 -> 17
m317_continuity_surface: fail, success_drop_count 17 -> 15
m314_continuity_surface: fail, success_drop_count 17 -> 15
```

Both source-diverse diagnostic failures are on rows corresponding to the
M267/M264 row 15 and row 16 family. This supports the interpretation that the
controlled-fusion candidate direction is preserving normal behavior while
eroding a current-family wrong-history failure branch.

Old-key neighborhood remains diagnostic-only. M399 passes the compact old-key
neighborhood with `40/40` accepted cases. The candidate has `35/40` accepted
cases and `39/40` normal-success cases. Because M945 explicitly demoted old key
`9944` from singleton veto to diagnostic status, this is not the primary
failure, but it agrees with the proof-washout diagnosis.

## Decision

Do not run PPO from M944 alpha `0.0725`.
Do not promote the candidate.

M946 rejects the candidate as a public replay/proof candidate despite exact
objective compatibility and behavior-seed retention.

The next step should audit the failing M267/M264 and source-diverse rows before
any new training:

```text
m947-v4-public-base-controlled-fusion-candidate-failing-surface-audit
```
