from pathlib import Path
from ray.tune.registry import register_env
import numpy as np
from ray import tune
from ray.rllib.algorithms.ppo import PPOConfig
from typing import Dict
from ray.rllib.policy.policy import PolicySpec
import ray
from pathlib import Path
from ray.rllib.algorithms.algorithm import Algorithm
from tqdm import tqdm
import json
import time
import sys
import os


from stage_2_rl_env import Stage2RLEnv
import multiprocessing

n_users = int(sys.argv[1])
timestamp = int(sys.argv[2])

if n_users == 400:
    file_name = "2025-10-14_17-01-06"
elif n_users == 500:
    file_name = "2025-10-14_18-19-06"
elif n_users == 600:
    file_name = "2025-10-14_19-38-00"
elif n_users == 700:
    file_name = "2025-10-14_20-54-04"
elif n_users == 800:
    file_name = "2025-10-14_21-46-19"
elif n_users == 900:
    file_name = "2025-10-14_23-21-46"
elif n_users == 1000:
    file_name = "2025-10-15_00-24-32"
elif n_users == 1100:
    file_name = "2025-10-15_00-50-05"
elif n_users == 1200:
    file_name = "2025-10-15_01-20-43"
elif n_users == 1300:
    file_name = "2025-10-15_02-30-54"
elif n_users == 1400:
    file_name = "2025-10-15_03-35-29"
elif n_users == 1500:
    file_name = "2025-10-15_04-51-11"
elif n_users == 1600:
    file_name = "2025-10-15_06-00-09"
elif n_users == 1700:
    file_name = "2025-10-15_07-01-34"
elif n_users == 1800:
    file_name = "2025-10-15_08-24-52"
elif n_users >= 1900:
    file_name = "2025-10-15_09-49-05"

# file_name = "2025-10-15_09-49-05"

os.system("cp -r /home/gmalmeida/workspace/VR-CG_resource_allocation/ray_results/trained_agents/experiment_state-{}.json /home/gmalmeida/workspace/VR-CG_resource_allocation/ray_results/ray_ppo".format(file_name))
os.system("cp -r /home/gmalmeida/workspace/VR-CG_resource_allocation/ray_results/trained_agents/basic-variant-state-{}.json /home/gmalmeida/workspace/VR-CG_resource_allocation/ray_results/ray_ppo".format(file_name))

train = False
test = True
debug = False
checkpoint_frequency = 1
store_results_path = str(Path("./ray_results/").resolve())
agent_name = "ray_ppo"

simu_config = {
    "root_path": str(Path("./").resolve()),
    "n_CNs": 10,
    "n_GNBs": 10,
    "n_users": n_users,
    "initial_timestamp": timestamp,
    "end_timestamp": timestamp,
    "training_episodes": 100000,
    "training_epochs": 10,
}
test_steps = simu_config["n_users"] # * 100 # if want to test for 100 TTIs


def env_creator(env_config):
    env = Stage2RLEnv(
        root_path=env_config["root_path"],
        n_CNs=env_config["n_CNs"],
        n_GNBs=env_config["n_GNBs"],
        n_users=env_config["n_users"],
        initial_timestamp=env_config["initial_timestamp"],
        end_timestamp=env_config.get("end_timestamp", None),
    )
    return env


register_env("stage_2_rl_env", lambda config: env_creator(config))


def generate_policies() -> Dict[str, PolicySpec]:
    policies = {
        "cn_user": PolicySpec(),
        "path_user": PolicySpec(),
    }

    return policies


def policy_mapping_fn(agent_id, episode=None, worker=None, **kwargs):
    return agent_id


if train:
    num_cpus = multiprocessing.cpu_count()
    ray.init(num_gpus=0, num_cpus=num_cpus, local_mode=True)

    algo_config = (
        PPOConfig()
        .environment(env="stage_2_rl_env", env_config=simu_config)
        .multi_agent(
            policies=generate_policies(),
            policy_mapping_fn=policy_mapping_fn,
            count_steps_by="env_steps",
        )
        .env_runners(num_env_runners=1, num_gpus_per_env_runner=0)
        .learners(num_learners=1)
        .training(
            lr=0.0003,
            train_batch_size=2048,
            minibatch_size=64,
            num_epochs=10,
            gamma=0.99,
            lambda_=0.95,
            clip_param=0.2,
            entropy_coeff=0.01,
            vf_loss_coeff=0.5,
            grad_clip=0.5,
            vf_clip_param=np.inf,
            use_gae=True,
            kl_coeff=0,
            use_kl_loss=False,
            kl_target=0,
        )
        .rl_module(
            model_config={
                "fcnet_hiddens": [64, 64],
                "fcnet_activation": "relu",
            },
        )
        .api_stack(
            enable_rl_module_and_learner=False,
            enable_env_runner_and_connector_v2=False,
        )
    )
    stop = {
        "num_env_steps_sampled_lifetime": simu_config["n_users"]
        * simu_config["training_episodes"]
        * simu_config["training_epochs"],
    }

    tuner = tune.Tuner(
        "PPO",
        param_space=algo_config.to_dict(),
        run_config=tune.RunConfig(
            storage_path=store_results_path,
            name=agent_name,
            stop=stop,
            verbose=2,
            checkpoint_config=tune.CheckpointConfig(
                checkpoint_frequency=checkpoint_frequency,
                checkpoint_at_end=True,
                # num_to_keep=5,
                # checkpoint_score_attribute="tejhutheut",  # "ray/tune/env_runners/agent_episode_returns_mean/cn_user",
                checkpoint_score_order="max",
            ),
        ),
    )
    results = tuner.fit()
    print(results)

if test:
    users_location_per_TTI = {}
    GM_solution = {"Total_Cost": 0,
                   "time": 0,
                   "Used_CNs": [],
                   "users": {},
                   "migration_cost": 0}

    analysis = tune.ExperimentAnalysis(f"{store_results_path}/{agent_name}/")
    assert analysis.trials is not None, "Analysis trial is None"
    checkpoint = analysis.get_best_checkpoint(
        trial=analysis.trials[0], metric="env_runners/episode_return_mean", mode="max"
    )
    assert checkpoint is not None, "Checkpoint is None"
    tuner_agent = Algorithm.from_checkpoint(checkpoint)

    env = env_creator(simu_config)
    obs, _ = env.reset()  # Initial observation
    for episode in tqdm(range(test_steps), desc="Testing steps", unit="steps"):
        first_stage_solution = json.load(open("solutions/first_stage/QoE_aware_heuristic/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(env.n_CNs, env.n_GNBs, env.n_users, int(env.curr_timestamp)), 'r'))["solution"]
        solution_users = first_stage_solution["users"]
        users_latency = {}
        for user in solution_users:
            users_latency[user["ID"]] = max(user["latency_to_gNB"].values())
        start_time = time.time()
        action = {}
        assert isinstance(obs, dict), "Observations must be a dictionary."
        for (
            agent_id,
            agent_obs,
        ) in (
            obs.items()
        ):  # We iterate over the different agents to generate our action dictionary
            policy_id = policy_mapping_fn(agent_id)
            action[agent_id] = tuner_agent.compute_single_action(
                agent_obs,
                policy_id=policy_id,
                explore=False,
            )
        obs, reward, terminated, truncated, info = env.step(
            action
        )  # Applying the action in the environment
        cn_option_choice = np.argsort(action["cn_user"])
        for idx_option in cn_option_choice[::-1]:
            cn_choice = idx_option + 1

        end_time = time.time()
        
        GM_user_ID = int(info["cn_user"]["curr_user"]) - 1
        GM_cn_choice = int(info["cn_user"]["cn_choice"])
        
        if env.curr_timestamp not in users_location_per_TTI.keys():
            users_location_per_TTI[env.curr_timestamp] = {}
        users_location_per_TTI[int(env.curr_timestamp)][GM_user_ID] = GM_cn_choice
        
        if GM_cn_choice not in GM_solution["Used_CNs"]:
            GM_solution["Used_CNs"].append(GM_cn_choice)

        GM_solution["users"][GM_user_ID] = {"max_latency": users_latency[GM_user_ID], "used_CN": GM_cn_choice}

        if int(env.curr_timestamp) - 1 in users_location_per_TTI.keys():
            if GM_user_ID in users_location_per_TTI[int(env.curr_timestamp) - 1].keys():
                if users_location_per_TTI[int(env.curr_timestamp) - 1][GM_user_ID] != GM_cn_choice:
                    GM_solution["migration_cost"] += 0.5
        
        GM_solution["Total_Cost"] = GM_solution["migration_cost"] + float(info["cn_user"]["activation_cost"]) + float(info["path_user"]["curr_variable_cost"])

        GM_solution["time"] += end_time - start_time

        if len(users_location_per_TTI[int(env.curr_timestamp)]) == env.n_users:
            json.dump({"solution": GM_solution}, open("./solutions/second_stage/agent/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(env.n_CNs, env.n_GNBs, env.n_users, int(env.curr_timestamp)), 'w'), indent=4)
            GM_solution = {"Total_Cost": 0,
                   "time": 0,
                   "Used_CNs": [],
                   "users": {},
                   "migration_cost": 0}
        assert isinstance(terminated, dict), "Terminated must be a dictionary."
        if terminated["__all__"]:
            env.reset()

os.system("rm -r /home/gmalmeida/workspace/VR-CG_resource_allocation/ray_results/ray_ppo/experiment_state-{}.json".format(file_name))
os.system("rm -r /home/gmalmeida/workspace/VR-CG_resource_allocation/ray_results/ray_ppo/basic-variant-state-{}.json".format(file_name))