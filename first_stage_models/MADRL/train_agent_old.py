from first_stage import FirstStageEnv
from ray.rllib.connectors.env_to_module.flatten_observations import FlattenObservations
from ray.rllib.utils.test_utils import (
    add_rllib_example_script_args,
    run_rllib_example_script_experiment,
)
from ray.tune.registry import get_trainable_cls, register_env  # noqa


parser = add_rllib_example_script_args(
    default_iters=1000,
    default_timesteps=int(1e6),  # 1 milhão de passos, por exemplo
    default_reward=float("inf")  # nunca para por média de recompensa
)
parser.set_defaults(
    enable_new_api_stack=True,
    num_agents=2,
)


if __name__ == "__main__":
    args = parser.parse_args()

    assert args.num_agents == 2, "Must set --num-agents=2 when running this script!"

    # You can also register the env creator function explicitly with:
    register_env("first-agent-env", lambda cfg: FirstStageEnv(n_users=10, n_gNBs=10, NN="PPO"))

    base_config = (
        get_trainable_cls(args.algo)
        .get_default_config()
        .environment(
            "first-agent-env",
        )
        .env_runners(
            env_to_module_connector=lambda env: FlattenObservations(multi_agent=True),
        )
        .multi_agent(
            # Define two policies.
            policies={"image_agent", "association_agent"},
            # Map agent "image_agent" to policy "image_agent" and agent "association_agent" to policy
            # "association_agent".
            policy_mapping_fn=lambda agent_id, episode, **kw: agent_id,
        )
    )

    run_rllib_example_script_experiment(base_config, args)