# M24 Mixed Hard-Replay Training

Last updated: 2026-05-21

## Motivation

M23 proved that hard response-corpus oversampling can be wired cleanly into PPO,
but hard-only replay is too narrow. It trains against seven mined seeds and
quickly damages the ordinary obstacle-avoidance policy.

M24 keeps the clean actor contract and changes only the simulator reset sampler:
some resets come from the M22 hard response corpus, and the rest are ordinary
randomized obstacle-driver scenarios. The hard seed remains reset metadata only.
It is not visible to the actor, recurrent state, checkpoint metadata, or policy
inference API.

## Training Direction

M24 should start from `m21_503`, not from an M23 checkpoint. The M23 checkpoints
are evidence for the failure mode, not a foundation to preserve.

The first M24 implementation should:

- add a reset sampler that selects a hard-corpus seed with a configured
  probability and otherwise uses normal randomized reset seeds;
- keep `training_seed_csv` deterministic and simulator-only;
- record reset source in env info for debugging, not actor input;
- use a lower learning rate or shorter horizon than M23;
- save periodic checkpoints and select by gates instead of final checkpoint.

## Validation Gates

M24 should be judged against both response-dependence and ordinary driving:

- same-contract obstacle benchmark must stay at or above M21_503 success
  (`0.500`);
- M22 hard actuator nominal success should remain at `1.000`, or perturbed
  success should improve beyond M21_503 (`0.714`);
- response-mask or recurrent-reset degradation must remain visible on the hard
  gate;
- final checkpoint drift is not acceptable if an earlier periodic checkpoint is
  better.

## Clean Contract

No compatibility path should be added for old observation shapes or old
checkpoints. If a checkpoint does not match the current model contract, it should
fail strictly. This project is still in research construction, so preserving
stale artifacts is less important than keeping the policy interface correct.
