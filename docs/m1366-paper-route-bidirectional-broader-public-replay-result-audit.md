# M1366 Paper-Route Bidirectional Broader Public Replay Result Audit

## Summary

M1366 audits the M1365 broader public replay pass.

Decision:

```text
bidirectional_broader_public_replay_audit_route_to_branch_synthesis
```

M1365 is a strong public diagnostic pass, but this branch has reached the
workflow synthesis cadence. The next step should synthesize M1357-M1366 before
promotion-gate design, PPO, private holdout, or another local experiment.

## Evidence

Candidate checkpoint:

```text
runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
```

M1365 passed:

```text
six public replay surfaces: 6 / 6
source-diverse protected diagnostic: pass
behavior seeds 9505 and 9506: pass
actor input contract: unchanged
```

Behavior details:

```text
seed 9505 candidate success delta: 0.0
seed 9506 candidate success delta: 0.0
reset >= zero_all ordering: true
```

Old-key neighborhood remained diagnostic-only:

```text
base accepted cases: 24 / 40
candidate accepted cases: 25 / 40
```

## Supported Claim

The supported claim is:

```text
M1362 alpha 0.1 is a broad-public-replay-passing candidate relative to M1154.
```

This is stronger than the M1362 two-surface preflight claim.

## Remaining Limits

M1365 still does not establish:

```text
promotion
private holdout generalization
fresh scenario distribution performance
PPO continuation stability
paper-level statistical evidence
level3 anticipatory self-identification
```

## Route Decision

Do not jump directly to promotion or PPO. The branch
`paper_route_bidirectional_replay_active_set_retention` has now accumulated a
complete 10-milestone evidence arc:

```text
M1357 design bidirectional active set
M1358 export combined anchors
M1359 design probe
M1360 run raw bidirectional update
M1361 audit raw margin-gap miss
M1362 find replay-safe alpha 0.1
M1363 audit two-surface result
M1364 design broader replay
M1365 pass broader replay
M1366 audit broader replay pass
```

M1367 should synthesize this branch and decide whether the next branch is:

```text
promotion-gate design
fresh scenario/generalization design
protected-surface refresh
PPO continuation admission
```

## Guardrails

M1366 performs no training, PPO, actor update, replay run, private holdout,
promotion, threshold relaxation, actor-input expansion, high-fidelity claim,
paper-level claim, or closed-loop self-identification claim.

## Next

```text
m1367-paper-route-bidirectional-active-set-retention-branch-synthesis
```
