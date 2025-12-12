import gymnasium as gym
from ray.rllib.env.multi_agent_env import MultiAgentEnv
import json
import numpy as np
import random
import os
import time

class FirstStageEnv(MultiAgentEnv):
    """
    Custom Multi Agent Environment for controlling resolution and FPS for n users, and .
    Resolution options: 1080p, 2K, 4K
    FPS options: 30, 60, 120
    """
    def __init__(self, n_users, n_gNBs, NN):
        super().__init__()
        # Define the number of agents in the DRL environment
        self.agents = self.possible_agents = ["image_agent", "association_agent"]
        # Define the number of gNBs in the network
        self.n_gNBs = n_gNBs
        # Define the number of users in the network
        self.n_users = n_users
        # Define the timestamp of user's positioning
        self.timestamp = 0
        # Define the ID of the user that is being solved
        self.solved_user = 0
        # Define the number of PRBs available in the gNBs (273 PRBs during 2000 TTIs)
        self.n_PRBs = 273 * 2000
        # Define the number of penalties in the episode
        self.episode_penalty = 0
        # Stores the reward history in JSON format - used to plot the results
        self.reward_histoty_json = {"FirstAgentReward": [], "SecondAgentReward": []}
        # Define the total reward in the episode
        self.total_reward = 0
        # Define the number of episodes finished, used to save the log files (save in each episode is time consuming)
        self.count_log = 0
        # state information used to calculate the reward function of second agent
        self.state = None
        # Define the available PRBs in the gNBs - empty at the beginning and initialized in the reset function
        self.gNBsAvailablePRBs = []

        self.desired_resolution = 0
        self.feasible_resolution = 0
        
        # Get users priority based on game instance - if it is quality (priority = 1), if it is performance (priority = 0)
        self.users_priority = self.get_users_priority(n_users)

        # Get users device capacities - resolution and fps
        self.users_resolution, self.users_fps = self.get_users_devices(n_users, n_gNBs)

        # Mapping from integers to real values
        self.res_mapping = {0: "1080p", 1: "2K", 2: "4K"}
        self.fps_mapping = {0: 30, 1: 60, 2: 120}

        self.observation_spaces = {
            "image_agent": gym.spaces.Box(low=0, high=3, shape=(2,),  dtype=np.int64),
            "association_agent": gym.spaces.Dict({"SEs": gym.spaces.Box(low=0, high=8, shape=(self.n_gNBs,),  dtype=np.float64),
                                                 "PRBs": gym.spaces.Box(low=0, high=1, shape=(self.n_gNBs,), dtype=np.float64)
                                                 })
        }
        
        self.action_spaces = {
            "image_agent": gym.spaces.MultiDiscrete([3, 3]),  # 3 resolutions and 3 FPS options
            "association_agent": gym.spaces.MultiDiscrete([self.n_gNBs, self.n_gNBs, self.n_gNBs])  # 3 gNBs as the maximum multi-connectivity limit
        }
    
    def reset(self, *, seed=None, options=None):
        # If the agent reaches the last timestamp of data, we reset the timestamp to 0
        # If not, we increase the timestamp by 1, i.e. goes to the next timestamp
        if self.timestamp == 99:
            self.timestamp = 0
        else:
            self.timestamp += 1
        
        # If reset is called, is because the episode has ended, i.e. the last user has been solved
        # Then we reset the solved user to the first one
        self.solved_user = 0

        # Reset the count  of episode penalties to zero
        self.episode_penalty = 0
        # Reset the total reward of the episode to zero
        self.total_reward = 0

        print(self.desired_resolution, self.feasible_resolution)
        self.desired_resolution = 0
        self.feasible_resolution = 0
        
        # If is time to plot the log, it will output it to the json log file
        # If its not, it will sum the count log to 1
        if self.count_log == 10:
            pass
        else:
            self.count_log += 1
        if os.path.exists("/home/gabriel/workspace/VR-CG_resource_allocation/input_files/users/{}_gNBs/{}_users_timestamp_{}.json".format(self.n_gNBs, self.n_users, self.timestamp)):
            users_json = json.load(open("/home/gabriel/workspace/VR-CG_resource_allocation/input_files/users/{}_gNBs/{}_users_timestamp_{}.json".format(self.n_gNBs, self.n_users, self.timestamp)))
        elif os.path.exists("/home/vmadmin/VR-CG_resource_allocation/input_files/users/{}_gNBs/{}_users_timestamp_{}.json".format(self.n_gNBs, self.n_users, self.timestamp)):
            users_json = json.load(open("/home/vmadmin/VR-CG_resource_allocation/input_files/users/{}_gNBs/{}_users_timestamp_{}.json".format(self.n_gNBs, self.n_users, self.timestamp)))
        users = users_json["users"]
        user_max_resolution = 0
        user_max_fps = 0
        for user in users:
            if user["ID"] == self.solved_user:
                user_SEs = [user["SE"][str(bs + 1)] for bs in range(self.n_gNBs)]
                if user["max_resolution"] == "1080p":
                    user_max_resolution = 0
                elif user["max_resolution"] == "2K":
                    user_max_resolution = 1
                elif user["max_resolution"] == "4K":
                    user_max_resolution = 2
                if user["max_frame_rate"] <= 30:
                    user_max_fps = 0
                elif user["max_frame_rate"] <= 60:
                    user_max_fps = 1
                elif user["max_frame_rate"] <= 120:
                    user_max_fps = 2
        self.gNBsAvailablePRBs = [self.n_PRBs for _ in range(self.n_gNBs)]
        observations = {
            "image_agent": np.array([user_max_resolution, user_max_fps]),
            "association_agent": {"SEs": np.array(user_SEs),
                                  "PRBs": np.array([1 for _ in range(self.n_gNBs)])},
        }

        self.state = observations

        return observations, {}  # <- empty infos dict

    def step(self, action_dict):
        # Get the image quality in a list [RES, FPS] from the action
        image_quality = action_dict["image_agent"]
        resolution = self.res_mapping[image_quality[0]]
        fps = self.fps_mapping[image_quality[1]]
        # Get the ID of the associated gNB from the action
        serving_gNB_1 = action_dict["association_agent"][0]
        serving_gNB_2 = action_dict["association_agent"][1]
        serving_gNB_3 = action_dict["association_agent"][2]
        
        # Calculate the reward for the first agent - based on the selected resolution, frame rate and gNB association
        first_agent_rw = self.first_agent_reward(resolution, fps)
        
        # Calculate the reward for the second agent - based on the user association action, selected resolution and frame rate
        second_agent_rw = self.second_agent_reward(serving_gNB_1, serving_gNB_2, serving_gNB_3, resolution, fps)
        self.solved_user += 1
        # If the episode is not done, goes to the next user
        # If it is finished, mantain the observation as the previous one - since it will be updated be the reset function
        if self.solved_user < self.n_users:
            observations = self.update_state(image_quality)
            self.state = observations
        else:
            observations = self.state
        
        # Compute rewards for each player based on the win-matrix.
        r1 = first_agent_rw
        r2 = second_agent_rw

        self.reward_histoty_json["FirstAgentReward"].append(r1)
        self.reward_histoty_json["SecondAgentReward"].append(r2)
        
        rewards = {"image_agent": r1, "association_agent": r2}

        if self.solved_user == self.n_users and self.count_log >= 5:
            self.count_log = 0
            # Save the reward history in JSON format
            if os.path.exists("/home/gabriel/workspace/VR-CG_resource_allocation/training_logs/{}_users_{}_gNBs_reward_history.json".format(self.n_users, self.n_gNBs)):
                json.dump(self.reward_histoty_json, open("/home/gabriel/workspace/VR-CG_resource_allocation/MADRL/training_logs/{}_users_{}_gNBs_reward_history.json".format(self.n_users, self.n_gNBs), "w"), indent=4)
            elif os.path.exists("/home/vmadmin/VR-CG_resource_allocation/training_logs/{}_users_{}_gNBs_reward_history.json".format(self.n_users, self.n_gNBs)):
                json.dump(self.reward_histoty_json, open("/home/vmadmin/VR-CG_resource_allocation/MADRL/training_logs/{}_users_{}_gNBs_reward_history.json".format(self.n_users, self.n_gNBs), "w"), indent=4)
        else:
            # Update the count_log variable
            self.count_log += 1


        # Terminate the entire episode (for all agents) once all users have being solved
        terminateds = {"__all__": self.solved_user == self.n_users}

        # Leave truncateds and infos empty.

        return observations, rewards, terminateds, {}, {}

    def get_users_priority(self, n_users):
        game_type = {}
        if os.path.exists("/home/gabriel/workspace/VR-CG_resource_allocation/input_files/games/{}_users_games_timestamp_{}.json".format(n_users, self.timestamp)):
            Games_list = json.load(open("/home/gabriel/workspace/VR-CG_resource_allocation/input_files/games/{}_users_games_timestamp_{}.json".format(n_users, self.timestamp), 'r'))["games"]
        elif os.path.exists("/home/vmadmin/VR-CG_resource_allocation/input_files/games/{}_users_games_timestamp_{}.json".format(n_users, self.timestamp)):
            Games_list = json.load(open("/home/vmadmin/VR-CG_resource_allocation/input_files/games/{}_users_games_timestamp_{}.json".format(n_users, self.timestamp), 'r'))["games"]
        for game in Games_list:
            game_type[game["ID"]] = game["game_type"]
        users_priority = {}
        if os.path.exists("/home/gabriel/workspace/VR-CG_resource_allocation/input_files/users/{}_gNBs/{}_users_timestamp_{}.json".format(self.n_gNBs, self.n_users, self.timestamp)):
            Users_list = json.load(open("/home/gabriel/workspace/VR-CG_resource_allocation/input_files/users/{}_gNBs/{}_users_timestamp_{}.json".format(self.n_gNBs, self.n_users, self.timestamp)))["users"]
        elif os.path.exists("/home/vmadmin/VR-CG_resource_allocation/input_files/users/{}_gNBs/{}_users_timestamp_{}.json".format(self.n_gNBs, self.n_users, self.timestamp)):
            Users_list = json.load(open("/home/vmadmin/VR-CG_resource_allocation/input_files/users/{}_gNBs/{}_users_timestamp_{}.json".format(self.n_gNBs, self.n_users, self.timestamp)))["users"]
        for user in Users_list:
            game_instance = user["game"]
            if game_type[game_instance] == "quality":
                users_priority[user["ID"]] = 1
            else:
                users_priority[user["ID"]] = 0
        for user in range(0, self.n_users):
            users_priority[user] = 1
        return users_priority

    def get_users_devices(self, n_users, n_gNBs):
        users_resolution = {}
        users_fps = {}
        if os.path.exists("/home/gabriel/workspace/VR-CG_resource_allocation/input_files/users/{}_gNBs/{}_users_timestamp_{}.json".format(self.n_gNBs, self.n_users, self.timestamp)):
            Users_list = json.load(open("/home/gabriel/workspace/VR-CG_resource_allocation/input_files/users/{}_gNBs/{}_users_timestamp_{}.json".format(self.n_gNBs, self.n_users, self.timestamp)))["users"]
        elif os.path.exists("/home/vmadmin/VR-CG_resource_allocation/input_files/users/{}_gNBs/{}_users_timestamp_{}.json".format(self.n_gNBs, self.n_users, self.timestamp)):
            Users_list = json.load(open("/home/vmadmin/VR-CG_resource_allocation/input_files/users/{}_gNBs/{}_users_timestamp_{}.json".format(self.n_gNBs, self.n_users, self.timestamp)))["users"]
        for user in Users_list:
            users_resolution[user["ID"]] = user["max_resolution"]
            users_fps[user["ID"]] = user["max_frame_rate"]
        
        return users_resolution, users_fps

    def first_agent_reward(self, resolution, fps):
        # alpha controls how strong is the penalty [1, 10]
        alpha = 1
        # set both reward to zero
        reward = 0
        # numeric value for the selected resolution
        res_to_number = {"1080p": 2, "2K": 4, "4K": 8}

        if self.users_priority[self.solved_user] == 1:
            if resolution == "4K" and self.users_resolution[self.solved_user] == "4K":
                reward = 1
                self.desired_resolution += 1
            elif reward == "2K" and self.users_resolution[self.solved_user] == "2K":
                reward = 1
                self.desired_resolution += 1
            elif resolution == "2K" and self.users_resolution[self.solved_user] == "4K":
                reward = 0.5
                self.feasible_resolution += 1
            elif resolution == "1080p" and self.users_resolution[self.solved_user] == "1080p":
                reward = 1
                self.desired_resolution += 1
            elif resolution == "1080p" and self.users_resolution[self.solved_user] == "2K":
                reward = 0.5
                self.feasible_resolution += 1
            elif resolution == "1080p" and self.users_resolution[self.solved_user] == "4K":
                reward = 0.25
                self.feasible_resolution += 1
            else:
                reward = (- alpha) * 1
                self.episode_penalty += 1
        else:    
            if fps == 120 and self.users_fps[self.solved_user] >= 120:
                reward = 1
            elif fps == 60 and 60 <= self.users_fps[self.solved_user] < 120:
                reward = 1
            elif fps == 60 and self.users_fps[self.solved_user] >= 120:
                reward = 0.5
            elif fps == 30 and 30 <= self.users_fps[self.solved_user] < 60:
                reward = 1
            elif fps == 30 and 60 <= self.users_fps[self.solved_user] < 120:
                reward = 0.5
            elif fps == 30 and self.users_fps[self.solved_user] >= 120:
                reward = 0.25
            else:
                reward = (- alpha) * 1
                self.episode_penalty += 1
        return reward
    
    def second_agent_reward(self, serving_gNB_1, serving_gNB_2, serving_gNB_3, resolution, fps):
        PRB_length = 0.36
        codec_bpp = 0.25
        routing_latency = 0.02

        association_agent_state = self.state["association_agent"]

        transmission_load = {"1080p": 1920 * 1080 * codec_bpp,
                             "2K": 2560 * 1440 * codec_bpp,
                             "4K": 3840 * 2160 * codec_bpp}
        
        # Determine the number of unique serving gNBs
        unique_gNBs = {serving_gNB_1, serving_gNB_2, serving_gNB_3}
        n_serving_gNBs = len(unique_gNBs)
        for gNB in unique_gNBs:
            used_PRBs_throughput = int(np.ceil(((transmission_load[resolution]*fps)/n_serving_gNBs) / ((PRB_length * 10 ** 6) * association_agent_state["SEs"][gNB])))
            proc_latency = ((transmission_load[resolution]/n_serving_gNBs)/1024)/(100*10**6)
            used_PRBs_latency = int(np.ceil((((transmission_load[resolution]*fps)/n_serving_gNBs)/(1 - (routing_latency + proc_latency)))/((PRB_length * 10 ** 6) * association_agent_state["SEs"][gNB])))
            used_PRBs = max(used_PRBs_throughput, used_PRBs_latency)
            # print("User {} in gNB {}, used PRBs {} to load {} with throughput {}".format(self.solved_user, gNB, used_PRBs, transmission_load[res]/n_serving_gNBs, ((PRB_length * 10 ** 6) * association_agent_state["SEs"][0][gNB] * used_PRBs)))
            # Check if the action is valid - if it is update the gNBs available PRBs
            if self.gNBsAvailablePRBs[gNB] >= used_PRBs:
                self.gNBsAvailablePRBs[gNB] -= used_PRBs
                reward = 1
            else:
                reward = -1
                self.episode_penalty += 1
        
        return reward
    
    def update_state(self, image_quality):
        # Generate next state with the SE of next user and the next action space
        if os.path.exists("/home/gabriel/workspace/VR-CG_resource_allocation/input_files/users/{}_gNBs/{}_users_timestamp_{}.json".format(self.n_gNBs, self.n_users, self.timestamp)):
            users_json = json.load(open("/home/gabriel/workspace/VR-CG_resource_allocation/input_files/users/{}_gNBs/{}_users_timestamp_{}.json".format(self.n_gNBs, self.n_users, self.timestamp)))
        elif os.path.exists("/home/vmadmin/VR-CG_resource_allocation/input_files/users/{}_gNBs/{}_users_timestamp_{}.json".format(self.n_gNBs, self.n_users, self.timestamp)):
            users_json = json.load(open("/home/vmadmin/VR-CG_resource_allocation/input_files/users/{}_gNBs/{}_users_timestamp_{}.json".format(self.n_gNBs, self.n_users, self.timestamp)))
        users = users_json["users"]
        user_SEs = []
        # Update the state for the next step
        for user in users:
            if user["ID"] == self.solved_user:
                user_SEs = [user["SE"][str(bs + 1)] for bs in range(self.n_gNBs)]
        available_PRBs_nomalized = []
        for gNB in range(self.n_gNBs):
            available_PRBs_nomalized.append(self.gNBsAvailablePRBs[gNB] / self.n_PRBs)
        
        observations = {
            "image_agent": np.array([image_quality[0], image_quality[1]]), 
            "association_agent": {
                "SEs": np.array(user_SEs),
                "PRBs": np.array(available_PRBs_nomalized)
            }
        }

        return observations