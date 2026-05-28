import numpy as np

from autodrift.env import DriftEnvConfig
from autodrift.evaluate import ActorPolicy


class FakeRecurrentModel:
    is_online_recurrent = True
    action_sequence_horizon = 1

    def __init__(self) -> None:
        self.hidden_inputs = []

    def act_recurrent(self, observation, hidden, deterministic=True):
        del observation, deterministic
        self.hidden_inputs.append(hidden)
        return np.zeros(3, dtype=np.float32), None, None, "next_hidden"


def test_actor_policy_carries_episode_persistent_hidden() -> None:
    model = FakeRecurrentModel()
    policy = ActorPolicy(model, DriftEnvConfig(), reset_hidden_policy="episode_persistent")
    policy.hidden = "existing_hidden"

    policy.act(np.zeros(72, dtype=np.float32), {})

    assert model.hidden_inputs == ["existing_hidden"]
    assert policy.hidden == "next_hidden"


def test_actor_policy_resets_every_step_control_hidden() -> None:
    model = FakeRecurrentModel()
    policy = ActorPolicy(model, DriftEnvConfig(), reset_hidden_policy="every_step_control")
    policy.hidden = "existing_hidden"

    policy.act(np.zeros(72, dtype=np.float32), {})

    assert model.hidden_inputs == [None]
    assert policy.hidden == "next_hidden"
