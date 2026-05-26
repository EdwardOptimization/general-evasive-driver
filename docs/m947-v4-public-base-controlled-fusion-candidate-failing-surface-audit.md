# M947 V4 Public Base Controlled Fusion Candidate Failing Surface Audit

## Purpose

M946 rejected the M944 alpha `0.0725` controlled-fusion candidate at the
closed-loop proof gate. M947 audits whether that failure is a single-alpha
overshoot, stale diagnostic artifact, or a real rejected-history branch
washout.

M947 does not train, run PPO, change actor inputs, or promote.

## Inputs

Primary M946 candidate:

```text
runs/m944_v4_public_base_controlled_fusion_candidate_compatibility/interpolation/checkpoints/alpha_0_0725.pt
```

M944 backup candidates:

```text
runs/m944_v4_public_base_controlled_fusion_candidate_compatibility/interpolation/checkpoints/alpha_0_0675.pt
runs/m944_v4_public_base_controlled_fusion_candidate_compatibility/interpolation/checkpoints/alpha_0_07.pt
```

Base:

```text
runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
```

## M946 Failure

M946 passed behavior retention but failed one public proof surface:

```text
public replay gates passed: 5 / 6
failed public replay surface: M267/M264
M267/M264 success_drop_count: 17 -> 13
behavior seeds 9505/9506: pass
actor_inputs_changed: false
training_started: false
ppo_used: false
promoted: false
```

The failing M267/M264 rows are:

| row_id | pair | left_step | right_step | base wrong margin | alpha 0.0725 wrong margin | wrong margin delta |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 6 | `9530:15:9550:18` | 15 | 18 | -0.000267 | 0.000576 | 0.000843 |
| 13 | `9530:9:9550:9` | 9 | 9 | -0.001118 | 0.000377 | 0.001495 |
| 15 | `9530:21:9550:21` | 21 | 21 | -0.000203 | 0.000556 | 0.000759 |
| 16 | `9530:6:9550:6` | 6 | 6 | -0.000708 | 0.000934 | 0.001642 |

All four rows keep normal-history success. The failure is that wrong-history
continuations cross from collision/negative margin into safe positive margin.
That erodes the self-ID proof row: the policy no longer behaves differently
enough under rejected history on those cases.

## Backup Alpha Audit

M947 ran no-training targeted replay on the same M267/M264 surface for the two
M944 backup candidates.

```bash
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
python -m autodrift.boundary_outcome_replay_gate \
  --checkpoint-policy m399_base=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --checkpoint-policy m944_a0675=runs/m944_v4_public_base_controlled_fusion_candidate_compatibility/interpolation/checkpoints/alpha_0_0675.pt \
  --corpus-csv runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --baseline-policy m399_base \
  --candidate-policy m944_a0675 \
  --run-dir runs/m947_v4_public_base_controlled_fusion_candidate_failing_surface_audit/m267_m264_a0675 \
  --device cpu
```

The same command was run for `alpha_0_07.pt`.

Results:

| candidate | gate pass | success_drop_count | failed rows |
| --- | --- | ---: | --- |
| alpha 0.0675 | false | 13 / 17 | 6, 13, 15, 16 |
| alpha 0.0700 | false | 13 / 17 | 6, 13, 15, 16 |
| alpha 0.0725 | false | 13 / 17 | 6, 13, 15, 16 |

Lowering to the known M944 backup candidates does not recover the proof gate.
This is not a single-alpha overshoot at `0.0725`.

## Source-Diverse Overlap

M946 source-diverse diagnostics are consistent with the same row family:

```text
current_m333_surface: pass, success_drop_count 17 -> 17
m317_continuity_surface: fail, success_drop_count 17 -> 15
m314_continuity_surface: fail, success_drop_count 17 -> 15
```

The source-diverse failures are:

| surface | failed rows | failed pair family |
| --- | --- | --- |
| M317 continuity | 15, 16 | `9530:21:9550:21`, `9530:6:9550:6` |
| M314 continuity | 15, 16 | `9530:21:9550:21`, `9530:6:9550:6` |

This is source-overlap evidence, not a stale singleton. The candidate direction
pushes a current-family rejected-history branch toward safety while also
improving normal margins.

## Old-Key Diagnostic

Old key `9944` remains diagnostic-only, as required by M945.

```text
M399 old-key compact accepted cases: 40 / 40
M944 alpha 0.0725 accepted cases: 35 / 40
M944 alpha 0.0725 normal-success cases: 39 / 40
```

This is not the formal veto, but it agrees with the broader diagnosis: the
candidate changes boundary behavior in fragile proof rows.

## Classification

The M946/M947 failure is:

```text
failure_type: proof_washout
failure_mode: rejected_history_branch_washout
alpha_overshoot_only: false
known_backup_alpha_repair: false
behavior_regression: false
contract_violation: false
```

Supported claims:

- M944 alpha `0.0725` is exact-objective compatible but not closed-loop
  replay/proof compatible.
- The known M944 backup candidates `0.0675` and `0.0700` fail the same M267/M264
  rows.
- The failure is concentrated in rejected/wrong-history branch safety, not in
  normal-history success or broad behavior-seed retention.
- Source-diverse diagnostics show overlap with the same row family, especially
  rows `15` and `16`.

Unsupported claims:

- M944 alpha `0.0725` is promotable.
- A smaller known backup alpha is enough.
- PPO can be run safely from this candidate.
- Exact objective compatibility is sufficient replay proof.

## Decision

Do not run PPO.
Do not promote any M944 controlled-fusion candidate.
Do not route directly to a lower-alpha replay gate, because both known backup
alphas fail the same public proof rows.

The next step should design a controlled-fusion repair objective or gate that
explicitly protects rejected-history terminal sign / unsafe-branch retention on
the M267/M264 row family before any full replay gate:

```text
m948-v4-public-base-controlled-fusion-rejected-branch-retention-design
```

The design should keep the same actor-input and trainable-surface contract:
actor inputs unchanged; response/context encoders, online GRU, critic, and
log_std frozen unless a later synthesis explicitly opens them.
