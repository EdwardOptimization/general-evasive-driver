# M3272 Phase-5 H2 Dynamic-Prefix Recovery Certificate

Date: 2026-07-10

## Decision

**Completed / no strict witness at canonical quick; full was not run.** Four of
five continuously reached branch states passed the preregistered slide truth
and matched-state gates, but the expanded steering-capable policy set did not
improve the best recovery time at any eligible branch. The quick strict-witness
gate failed and blocks full.

## Protocol health

M3272 replays the hash-frozen M3266 Chrono/TMeasy slide-entry action from a
straight state and branches without reset. For every branch and policy, body,
wheel, tire-relaxation, and road states therefore share the same continuous
history.

The following gates passed:

- 150/150 expected candidate rows;
- physical zero-pedal semantics and exact 6-in-30 policy nesting;
- identical prefix and branch-state hashes across every policy;
- finite observations and complete four-wheel tire truth;
- weak recovery-set inclusion by construction;
- 10/10 selected baseline/expanded winner replays exactly matched.

The source prefix contains simultaneous-pedal segments. It is used only as a
common state generator and is not part of either compared recovery policy set.

## Quick results

| branch time | beta | rear slip | eligible | best baseline | baseline time | best expanded | advantage |
|---:|---:|---:|---|---|---:|---|---:|
| 0.60 s | -0.244 | 0.335 | yes | 25% throttle | 1.58 s | same baseline | 0.00 s |
| 0.90 s | -0.395 | 0.482 | yes | 25% throttle | 1.06 s | same baseline | 0.00 s |
| 1.20 s | -0.317 | 0.359 | yes | 25% throttle | 0.52 s | same baseline | 0.00 s |
| 1.50 s | -0.209 | 0.156 | yes | full uniform brake | 0.12 s | same baseline | 0.00 s |
| 1.80 s | +0.096 | 0.205 | no, beta dwell ended | not evaluated | - | - | - |

At the first two branches, neither coast nor uniform braking recovered, but a
zero-steer 25% throttle policy did. At the later branches, coast or uniform
braking also recovered. Added countersteer was never the best recovery policy.

## Inference

M3272 corrects M3271's injected-tire-state defect and supplies valid negative
evidence. It shows that being in a real moderate slide is not by itself
sufficient to require active drift steering: longitudinal action alone recovered
all four eligible states in this signed Chrono entry family.

The result does not prove that steering never expands post-slip recovery. It
does prove that the proposed broad statement, "once sliding, drift control is
needed," is too strong. Strict post-slip value, if it exists, must be scoped to
deeper or otherwise unrecoverable slide states. No further local Chrono policy
or threshold repair is admitted.
