import gymnasium as gym
import json
from classes import CN, GNB, GAME, USER, PATH
import numpy as np
from ray.rllib.env.multi_agent_env import MultiAgentEnv
from copy import deepcopy
from pathlib import Path


class Stage2RLEnv(MultiAgentEnv):
    """
    Custom reinforcement learning environment for stage 2.
    This class extends the gym.Env class to create a specific environment.
    """

    def __init__(
        self, root_path, n_CNs, n_GNBs, n_users, initial_timestamp, end_timestamp=None
    ):
        super(Stage2RLEnv, self).__init__()
        self.root_path = root_path
        self.n_CNs = n_CNs
        self.n_GNBs = n_GNBs
        self.n_users = n_users
        self.initial_timestamp = initial_timestamp
        self.end_timestamp = end_timestamp
        self.curr_timestamp = initial_timestamp
        self.curr_placement = {}
        self.curr_user = 0
        self.delta_max = 1 * 1000  # 1 second in milliseconds
        self.max_number_paths = 5  # Maximum number of paths between a CN and a gNB
        self.enable_one_path_per_flow = False  # Enable one path per flow
        self.limited_resources = False  # Enable limited resources in CNs and paths
        self.action_space = gym.spaces.Dict(
            {
                "path_user": gym.spaces.Box(
                    low=0,
                    high=1,
                    shape=(self.max_number_paths,),
                ),
                "cn_user": gym.spaces.Box(
                    low=0,
                    high=1,
                    shape=(n_CNs,),
                ),
            }
        )
        self.observation_space = gym.spaces.Dict(
            {
                "cn_user": gym.spaces.Box(
                    low=0,
                    high=np.inf,
                    shape=(4 + n_CNs,),
                ),
                "path_user": gym.spaces.Box(
                    low=0,
                    high=1,
                    shape=(self.max_number_paths * 2,),
                ),
            }
        )
        self.agents = ["cn_user", "path_user"]
        self.init_timestamp(self.curr_timestamp, n_users)

    def init_timestamp(self, timestamp, n_users):
        # read input files
        (
            self.CNs,
            self.GNBs,
            self.Games,
            self.Users,
            self.Paths,
            self.Links,
            self.Links_latency,
            self.Links_bandwidth,
        ) = self.read_input_files(self.n_CNs, self.n_GNBs, self.n_users, timestamp)

        # get user's computational requirements based on image quality and throughput
        if n_users <= 300:
            self.sol = json.load(
                # open(
                #     "{}/solutions/first_stage/optimal_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(
                #         self.root_path, self.n_CNs, self.n_GNBs, self.n_users, timestamp
                #     ),
                #     "r",
                # )
                open(
                    "/home/gmalmeida/workspace/VR-CG_resource_allocation/solutions/first_stage/optimal_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(
                        self.n_CNs, self.n_GNBs, self.n_users, timestamp
                    ),
                    "r",
                )
            )
        else:
            self.sol = json.load(
                open(
                    "{}/solutions/first_stage/QoE_aware_heuristic/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(
                        self.root_path, self.n_CNs, self.n_GNBs, self.n_users, timestamp
                    ),
                    "r",
                )
            )

        (
            self.users_CPU_demand,
            self.users_RAM_demand,
            self.users_GPU_demand,
            self.users_total_load,
            self.users_load_to_gNB,
            self.users_latency_to_gNB,
        ) = self.get_users_game_requirements(self.Users, self.Games, self.sol)

        if self.enable_one_path_per_flow:
            new_Paths_IDs = []

            for user in self.Users:
                for gNB in self.users_load_to_gNB[user.my_ID()].keys():
                    for cn in self.CNs:
                        min_path_length = 99999
                        min_path_id = -1
                        for p in self.Paths:
                            if str(p.destination) == gNB and p.source == cn.ID:
                                if len(p.my_links_list()) < min_path_length:
                                    if min_path_id != -1:
                                        new_Paths_IDs.remove(min_path_id)
                                    min_path_length = len(p.my_links_list())
                                    min_path_id = p.ID
                                    new_Paths_IDs.append(p.ID)
            new_Paths = []
            for i in new_Paths_IDs:
                for p in self.Paths:
                    if p.ID == i and p not in new_Paths:
                        new_Paths.append(p)

            self.Paths = new_Paths

        self.links_resource_usage = deepcopy(self.Links_bandwidth)
        self.variable_cost = np.zeros((self.n_CNs,))
        self.used_cns = []
        self.max_variable_costs = np.max(
            [
                [
                    cn.Variable_cost["CPU"],
                    cn.Variable_cost["GPU"],
                    cn.Variable_cost["RAM"],
                    cn.Variable_cost["NET"],
                ]
                for cn in self.CNs
            ],
            axis=0,
        )
        self.max_latency = np.max([path.latency for path in self.Paths])

        # TODO Recalculate these max costs based on all timestamps
        self.max_cpu_cost = self.max_variable_costs[0] * np.max(
            list(self.users_CPU_demand.values())
        )
        self.max_gpu_cost = self.max_variable_costs[1] * np.max(
            list(self.users_GPU_demand.values())
        )
        self.max_ram_cost = self.max_variable_costs[2] * np.max(
            list(self.users_RAM_demand.values())
        )

    def reset(self, seed=None, options=None):
        """
        Reset the environment to an initial state.
        Returns the initial observation.
        """
        # Initialize state and return initial observation
        self.curr_user = 0
        obs = {
            "cn_user": np.zeros((4 + self.n_CNs,)),
            "path_user": np.zeros((self.max_number_paths * 2,)),
        }
        info = {}
        if self.end_timestamp is not None:
            if self.curr_timestamp < self.end_timestamp:
                self.curr_timestamp += 1
                self.init_timestamp(self.curr_timestamp, self.n_users)
            else:
                self.curr_timestamp = self.initial_timestamp
        self.links_resource_usage = deepcopy(self.Links_bandwidth)
        self.variable_cost = np.zeros((self.n_CNs,))

        return obs, info

    def step(self, ori_action):
        path_choice = None
        dst_gnb = int(list(self.users_load_to_gNB[self.curr_user].keys())[0])
        ue_load = self.users_load_to_gNB[self.curr_user][str(dst_gnb)] / 1e6  # Mbits

        action = deepcopy(ori_action)
        action["cn_user"][dst_gnb - 1] = 0

        cn_option_choice = np.argsort(action["cn_user"])
        for idx_option in cn_option_choice[::-1]:
            cn_choice = idx_option + 1

            # Check the valid paths between the chosen CN and gNB that the user is associated with
            path_option_choice = [
                idx
                for idx, path in enumerate(self.Paths)
                if path.source == cn_choice and path.destination == dst_gnb
            ]
            path_option_choice = np.array(path_option_choice[: self.max_number_paths])
            if len(path_option_choice) == 0:
                continue
            paths_priority = path_option_choice[
                np.argsort(-action["path_user"][0 : len(path_option_choice)])
            ]
            for idx_path_option in paths_priority: # AGENTE VERIFICANDO SE OS CAMINHOS SAO VALIDOS (AVALIAR DEPOIS)
                path_availability = np.all(
                    [
                        self.links_resource_usage[link] >= ue_load
                        for link in self.Paths[idx_path_option].links_list
                    ]
                )
                if (
                    path_availability
                    and self.Paths[idx_path_option].latency <= self.delta_max
                ):  # Check if the path has enough resources and the latency is acceptable
                    path_choice = idx_path_option
                    for link in self.Paths[idx_path_option].links_list:
                        self.links_resource_usage[link] -= ue_load
                    break
            if path_choice is not None:
                if (cn_choice) not in self.used_cns:
                    self.used_cns.append(cn_choice)
                break

        assert (
            path_choice is not None
        ), f"No valid path found for user {self.curr_user} on Timestamp {self.curr_timestamp} with source {cn_choice} and destination {dst_gnb} and option paths {path_option_choice}. Path availabilyty: {path_availability} and Latency: {self.Paths[idx_path_option].latency <= self.delta_max}"

        # Reward calculation
        (reward, activation_cost, migration_cost, curr_variable_cost) = self.get_reward(
            dst_gnb=dst_gnb, cn_choice=cn_choice
        )

        next_user = self.curr_user + 1 if self.curr_user + 1 < self.n_users else 0
        obs = self.get_observation(next_user, path_option_choice)
        self.curr_user += 1
        global_terminated = self.curr_user == self.n_users
        terminated = {"cn_user": global_terminated, "path_user": global_terminated}
        truncated = {"cn_user": global_terminated, "path_user": global_terminated}
        terminated["__all__"], truncated["__all__"] = (
            global_terminated,
            global_terminated,
        )
        self.curr_placement[int(self.curr_user) - 1] = int(cn_choice)
        info = {
            "cn_choice": cn_choice,
            "path_choice": path_choice,
            "links_resource_usage": self.links_resource_usage,
            "users_CPU_demand": self.users_CPU_demand,
            "users_RAM_demand": self.users_RAM_demand,
            "users_GPU_demand": self.users_GPU_demand,
            "users_total_load": self.users_total_load,
            "users_load_to_gNB": self.users_load_to_gNB,
            "users_latency_to_gNB": self.users_latency_to_gNB,
            "variable_cost": self.variable_cost,
            "curr_user": self.curr_user,
            "activation_cost": activation_cost,
            "migration_cost": migration_cost,
            "curr_variable_cost": curr_variable_cost,
            "reward": reward,
        }
        info_agents = {"cn_user": info, "path_user": info}

        # print(
        #     f"Terminated: {terminated['__all__']}, Reward: {reward}, Curr user: {info['curr_user']}"
        # )

        return obs, reward, terminated, truncated, info_agents

    def get_reward(self, dst_gnb, cn_choice):
        max_fixed_cost = np.max([cn.Fixed_cost for cn in self.CNs])
        max_fixed_cost = max_fixed_cost if max_fixed_cost > 0 else 1
        activation_cost = np.sum(
            [
                cn.Fixed_cost / max_fixed_cost
                for cn in self.CNs
                if cn.ID in self.used_cns
            ]
        )
        # Migration cost is not considered in this stage
        migration_cost = 0

        if int(self.curr_user) - 1 in self.curr_placement.keys():
            if self.curr_placement[int(self.curr_user) - 1] != cn_choice:
                migration_cost = 0.5  # Fixed migration cost

        # Variable cost
        cn_variable_cost = np.array(
            [cn.Variable_cost for cn in self.CNs if cn.ID == cn_choice]
        )[0]
        normalized_cpu = (
            self.users_CPU_demand[self.curr_user]
            * cn_variable_cost["CPU"]
            / self.max_cpu_cost
        )
        normalized_gpu = (
            self.users_GPU_demand[self.curr_user]
            * cn_variable_cost["GPU"]
            / self.max_gpu_cost
        )
        normalized_ram = (
            self.users_RAM_demand[self.curr_user]
            * cn_variable_cost["RAM"]
            / self.max_ram_cost
        )
        curr_variable_cost = normalized_cpu + normalized_gpu + normalized_ram
        self.variable_cost[cn_choice - 1] = curr_variable_cost

        reward = -(activation_cost + migration_cost + curr_variable_cost)

        dict_reward = {"cn_user": reward, "path_user": reward}
        # print(
        #     f"User {self.curr_user}, Chosen CN {cn_choice} Reward: ",
        #     self.variable_cost[self.curr_user],
        #     "CPU cost: ",
        #     normalized_cpu,
        #     "GPU cost: ",
        #     normalized_gpu,
        #     "RAM cost: ",
        #     normalized_ram,
        #     "NET cost: ",
        #     normalized_net,
        # )
        return (dict_reward, activation_cost, migration_cost, curr_variable_cost)

    def get_observation(self, user, path_option_choice):
        # CN user observation
        user_info = [
            self.users_CPU_demand[user] / np.max(list(self.users_CPU_demand.values())),
            self.users_RAM_demand[user] / np.max(list(self.users_RAM_demand.values())),
            self.users_GPU_demand[user] / np.max(list(self.users_GPU_demand.values())),
            self.users_total_load[user] / np.max(list(self.users_total_load.values())),
        ]

        obs_cn_user = np.append(user_info, self.variable_cost)

        # Path observation
        chosen_path_resource_usage = np.array(
            [
                np.min(
                    [
                        (self.Links_bandwidth[link] - self.links_resource_usage[link])
                        / self.Links_bandwidth[link]
                        for link in self.Paths[path_option].links_list
                    ]
                )
                for path_option in path_option_choice
            ]
        )
        chosen_path_resource_usage = np.pad(
            chosen_path_resource_usage,
            (0, self.max_number_paths - len(chosen_path_resource_usage)),
            "constant",
            constant_values=1,
        )
        paths_latency = np.array(
            [self.Paths[idx].latency / self.max_latency for idx in path_option_choice]
        )
        paths_latency = np.pad(
            paths_latency,
            (0, self.max_number_paths - len(paths_latency)),
            "constant",
            constant_values=1,
        )
        obs_path_user = np.append(chosen_path_resource_usage, paths_latency)

        obs = {
            "cn_user": obs_cn_user,
            "path_user": obs_path_user,
        }

        return obs

    def get_users_priority(self, Users, Games):
        users_priority = {}
        for u in Users:
            if Games[u.my_game() - 1].my_game_type() == "quality":
                users_priority[u.my_ID()] = 1
            else:
                users_priority[u.my_ID()] = 0
        return users_priority

    def get_users_game_requirements(self, Users, Games, sol):
        flops_per_pixel = 440  # REF https://openaccess.thecvf.com/content/CVPR2023W/NTIRE/papers/Zamfir_Towards_Real-Time_4K_Image_Super-Resolution_CVPRW_2023_paper.pdf
        users_CPU_demand = {}
        users_RAM_demand = {}
        users_GPU_demand = {}
        users_total_load = {}
        users_load_to_gNB = {}
        users_latency_to_gNB = {}

        for user in Users:
            for g in Games:
                if g.my_ID() == user.my_game():
                    game = g
            users_CPU_demand[user.my_ID()] = game.my_CPU_requirement()
            users_RAM_demand[user.my_ID()] = game.my_RAM_requirement()
            for u in sol["solution"]["users"]:
                if u["ID"] == user.my_ID():
                    u_resolution = u["resolution"]
                    u_frame_rate = u["frame_rate"]
                    users_total_load[user.my_ID()] = u["total_load"]
                    users_load_to_gNB[user.my_ID()] = {}
                    users_latency_to_gNB[user.my_ID()] = {}
                    for gNB in u["load_to_gNB"]:
                        users_load_to_gNB[user.my_ID()][gNB] = u["load_to_gNB"][gNB]
                        users_latency_to_gNB[user.my_ID()][gNB] = u["latency_to_gNB"][
                            gNB
                        ]

            if u_resolution == "1080p":
                n_pixels = 1920 * 1080 * 2
            elif u_resolution == "2K":
                n_pixels = 2560 * 1440 * 2
            elif u_resolution == "4K":
                n_pixels = 3840 * 2160 * 2
            users_GPU_demand[user.my_ID()] = n_pixels * flops_per_pixel * u_frame_rate

        return (
            users_CPU_demand,
            users_RAM_demand,
            users_GPU_demand,
            users_total_load,
            users_load_to_gNB,
            users_latency_to_gNB,
        )

    def read_input_files(self, n_CNs, n_GNBs, n_users, timestamp):
        CNs_list = json.load(
            # open(
            #     "{}/input_files/topology/{}_gNBs.json".format(self.root_path, n_CNs),
            #     "r",
            # )
            open(
                "/home/gmalmeida/workspace/VR-CG_resource_allocation/input_files/topology/{}_gNBs.json".format(n_CNs),
                "r",
            )
        )["nodes"]
        CNs = []
        for cn in CNs_list:
            CNs.append(
                CN(
                    cn["ID"],
                    cn["CPU_capacity"],
                    cn["GPU_capacity"],
                    cn["RAM_capacity"],
                    cn["compression_ratio"],
                    cn["Network_capacity"],
                    cn["Fixed_cost"],
                    cn["Variable_cost"],
                )
            )

        GNBs_list = json.load(
            # open("{}/input_files/gNBs/{}_gNBs.json".format(self.root_path, n_GNBs), "r")
            open("/home/gmalmeida/workspace/VR-CG_resource_allocation/input_files/gNBs/{}_gNBs.json".format(n_GNBs), "r")
        )["gNBs"]
        GNBs = []
        for gnb in GNBs_list:
            GNBs.append(
                GNB(gnb["ID"], gnb["TX_power"], gnb["number_PRBs"], gnb["PRB_BW"])
            )

        Games_list = json.load(
            # open(
            #     "{}/input_files/games/{}_users_games_timestamp_{}.json".format(
            #         self.root_path, n_users, timestamp
            #     ),
            #     "r",
            # )
            open(
                "/home/gmalmeida/workspace/VR-CG_resource_allocation/input_files/games/{}_users_games_timestamp_0.json".format(
                    n_users, timestamp
                ),
                "r",
            )
        )["games"]
        Games = []
        for game in Games_list:
            Games.append(
                GAME(
                    game["ID"],
                    game["CPU_requirement"],
                    game["RAM_requirement"],
                    game["game_type"],
                )
            )

        Users_list = json.load(
            # open(
            #     "{}/input_files/users/{}_gNBs/{}_users_timestamp_{}.json".format(
            #         self.root_path, n_GNBs, n_users, timestamp
            #     ),
            #     "r",
            # )
            open(
                "/home/gmalmeida/workspace/VR-CG_resource_allocation/input_files/users/{}_gNBs/{}_users_timestamp_{}.json".format(
                    n_GNBs, n_users, timestamp
                ),
                "r",
            )
        )["users"]
        Users = []
        for user in Users_list:
            Users.append(
                USER(
                    user["ID"],
                    user["SE"],
                    user["game"],
                    user["game_instance"],
                    user["max_resolution"],
                    user["max_frame_rate"],
                )
            )

        Paths_list = json.load(
            # open(
            #     "{}/input_files/topology/{}_gNBs.json".format(self.root_path, n_GNBs),
            #     "r",
            # )
            open(
                "/home/gmalmeida/workspace/VR-CG_resource_allocation/input_files/topology/{}_gNBs.json".format(n_GNBs),
                "r",
            )
        )["paths"]
        Paths = []
        pathID = 0
        Links_latency = {}
        Links_bandwidth = {}
        for path in Paths_list:
            Paths.append(
                PATH(
                    pathID,
                    Paths_list[path]["path"][0],
                    Paths_list[path]["path"][len(Paths_list[path]["path"]) - 1],
                    Paths_list[path]["latency"],
                    Paths_list[path]["bandwidth"],
                    Paths_list[path]["links"],
                )
            )
            pathID += 1
        Links_list = json.load(
            # open(
            #     "{}/input_files/topology/{}_gNBs.json".format(self.root_path, n_GNBs),
            #     "r",
            # )
            open(
                "/home/gmalmeida/workspace/VR-CG_resource_allocation/input_files/topology/{}_gNBs.json".format(n_GNBs),
                "r",
            )
        )["links"]
        Links = []
        for link in Links_list:
            i = link["from"]
            j = link["to"]
            if (i, j) not in Links:
                Links.append((i, j))
                Links.append((j, i))
            Links_latency[(i, j)] = link["latency"]
            Links_latency[(j, i)] = link["latency"]
            Links_bandwidth[(i, j)] = link["bandwidth"]
            Links_bandwidth[(j, i)] = link["bandwidth"]

        return CNs, GNBs, Games, Users, Paths, Links, Links_latency, Links_bandwidth


def main():
    # Example usage
    env = Stage2RLEnv(
        root_path=str(Path("./").resolve()),
        n_CNs=10,
        n_GNBs=10,
        n_users=250,
        initial_timestamp=0,
        end_timestamp=99,
    )
    obs = env.reset()
    num_episodes = 10000
    for episode in range(num_episodes):
        terminated = {}
        terminated["__all__"] = False
        while not terminated["__all__"]:
            action = env.action_space.sample()
            next_obs, reward, terminated, truncated, info = env.step(action)
            env.observation_space.contains(next_obs)
            print(
                f"Episode: {episode}, Reward: {reward}, Curr user: {info['cn_user']['curr_user']}"
            )
        env.reset()


if __name__ == "__main__":
    main()
