# M382 Terminal-Margin Recovery Residual Design

M382 designs the next exact-repair residual after M381 showed the old-key
preference surrogate is misaligned with closed-loop cumulative old-key replay
tails. This is a design milestone only. It does not run PPO, promote a
checkpoint, lower old-key thresholds, or change actor inputs.

## Design Question

The current old-key surrogate improves as the closed-loop old-key lower tail
gets worse. The design question is:

```text
How can exact repair see the old-key replay-tail failure directly enough to
move the actor in a useful direction, without differentiating through the
simulator and without adding oracle inputs to the deployable actor?
```

## Current Surface Audit

Existing exact repair already has these pieces:

- `exact_post_ppo_repair.py` loads M297 preference snippets, M270 outcome
  snippets, and optional old-key preference snippets.
- The current old-key path uses log-prob preference plus action-anchor terms.
- `old_key_preference_corpus.py` can export deployable observation,
  preferred/rejected recurrent hidden states, preferred/rejected actions,
  terminal margins, row ids, and row weights.
- The replay gates remain authoritative for old-key proof: exact losses are
  only proposal filters, not promotion gates.

M381 proved the current exact old-key preference path is not enough:

```text
surrogate improvement vs replay gap p10 corr: -0.993196
surrogate improvement vs gap-p10 erosion corr: +0.991817
```

So the next residual must be tied to actual replay-tail recovery, not merely to
stronger old-key branch weighting.

## Options

| Option | Change | Upside | Downside | Decision |
| --- | --- | --- | --- | --- |
| V3 branch-weight overlay | Add more hard/gap-tail weights to old-key preference corpus | Smallest code change | M381 shows this objective moves opposite the replay tail | reject |
| Differentiable terminal-margin loss | Backpropagate through rollout terminal margin | Directly optimizes the right quantity | Large simulator/AD rewrite and high instability risk | reject for now |
| Learned terminal-margin critic | Train a separate critic on replay-tail rows and optimize it | Could be smoother than action targets | Adds model/critic reliability risk before basic recovery is proven | defer |
| Local-action recovery residual | Offline search a small action correction on tail rows, then anchor preferred branch to the recovered action | Small extension, replay-selected target, no actor-input change | One-step target is approximate and must still be replay-gated | choose |

## Chosen Design

Implement a training-only local-action recovery corpus for old-key tail rows.

For each row from the current failure tail, collect the same deployable
observation and recurrent hidden states already used by old-key preference
corpora:

```text
observation
preferred_hidden        # correct / normal history
rejected_hidden         # wrong-history branch, for anchoring only
base_preferred_action   # current promoted base action
base_rejected_action    # current promoted base wrong-history action
recovery_action         # offline one-step action selected by replay search
base_normal_margin
candidate_normal_margin
recovered_normal_margin
wrong_history_margin
case_id / row_id / weights
```

`recovery_action` is selected offline:

1. Start from the M379 public-gate base and M380 gap-tail rows.
2. At the old-key replay decision state, evaluate a small local action set
   around the base preferred action:
   - base preferred action;
   - failed candidate preferred action;
   - steer deltas such as `+-0.01`, `+-0.02`, `+-0.04`;
   - brake/throttle deltas such as `+-0.02`, `+-0.04`, clipped to action bounds;
   - optional low-discrepancy random deltas within a small L2 radius.
3. Roll out the rest of the case with the normal policy after the one-step
   override.
4. Select the action with the highest recovered normal terminal margin,
   breaking ties by smaller action L2 from the base action.
5. Accept the recovery row only if it improves normal terminal margin by a
   preregistered buffer, for example `>= 0.0002`, or preserves the current base
   when no useful local correction exists.

This uses simulator outcomes only to build training-time targets. The actor
still receives only the existing 72-dim human-view observation and recurrent
hidden state at deployment.

## Exact Loss Terms

Add an optional `old_key_recovery_npz` to exact repair. The first
implementation should add only one new loss term:

```text
L_recovery =
  mean_i w_i * || tanh(mean_pi(o_i, h_i^normal)) - a_i^recovery ||^2
```

with row weights:

```text
w_i =
  tail_severity_i
  * clip(recovered_margin_i - base_margin_i, min=0, max=margin_cap)
  / margin_cap
```

The wrong-history branch should not be made safer. Keep it anchored to the
current base wrong-history action:

```text
L_wrong_anchor =
  mean_i w_i * || tanh(mean_pi(o_i, h_i^wrong)) - a_i^base_wrong ||^2
```

The old-key recovery residual used by exact repair is:

```text
L_old_key_recovery = L_recovery + lambda_wrong_anchor * L_wrong_anchor
```

Then exact repair becomes:

```text
L_total =
  lexicographic hinges for M297 / M270
  + existing action anchor
  + parameter trust
  + lambda_old_key_recovery * L_old_key_recovery
```

The old-key preference surrogate may still be logged, but M383 should not use
it as the main driver if it conflicts with recovery. Closed-loop cumulative
old-key replay remains the authoritative proof gate.

## Acceptance Order

M383 should implement infrastructure and smoke tests only:

1. Export a recovery corpus from the M380 gap-tail rows.
2. Verify no-update exact repair can read it.
3. Verify `L_old_key_recovery` is finite and changes when recovery actions
   differ from base actions.
4. Run `make research-validate`.

M384 should be the first no-PPO proof probe:

1. Run exact repair from the M379 base toward the failing alpha `0.1` candidate
   with the recovery residual enabled.
2. Check exact M297/M270 no-regression.
3. Run cumulative old-key replay before source-diverse or first replay gates.
4. If cumulative old-key passes, run source-diverse and first replay gates.
5. Do not promote directly; admit a full public gate only after proof gates pass.

## Why This Preserves The Actor Contract

The new corpus is training-time metadata. It does not add `mu`, hidden vehicle
parameters, slip, oracle labels, TTC, path references, or controller-mode inputs
to the deployable actor. The deployed policy still maps:

```text
human-view observation + recurrent hidden -> steer / throttle / brake
```

The simulator is used only to choose better local action targets for the exact
repair objective, exactly as previous replay gates used simulator outcomes to
judge candidates.

## Risks

- One-step local recovery may not be enough if the tail failure requires a
  multi-step maneuver correction.
- Recovery targets can overfit the current public old-key rows, so M384 still
  needs source-diverse and first replay gates before any full public gate.
- If no local recovery improves margin, the right next step is a terminal-margin
  critic or short-horizon sequence target, not larger branch weights.

## Decision

Admit:

```text
m383-old-key-local-recovery-residual-implementation
```

Decision:

```text
admit_m383_old_key_local_recovery_residual_implementation
```
