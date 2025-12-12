from math import log2, log
from methods import read_input_files
import os
import sys
import json
import time

def get_users_game_requirements(Users, Games, sol):
    flops_per_pixel = 440 # REF https://openaccess.thecvf.com/content/CVPR2023W/NTIRE/papers/Zamfir_Towards_Real-Time_4K_Image_Super-Resolution_CVPRW_2023_paper.pdf
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
                    users_latency_to_gNB[user.my_ID()][gNB] = u["latency_to_gNB"][gNB]

        if u_resolution == "1080p":
            n_pixels = 1920 * 1080 * 2
        elif u_resolution == "2K":
            n_pixels = 2560 * 1440 * 2
        elif u_resolution == "4K":
            n_pixels = 3840 * 2160 * 2
        users_GPU_demand[user.my_ID()] = n_pixels * flops_per_pixel * u_frame_rate

    return users_CPU_demand, users_RAM_demand, users_GPU_demand, users_total_load, users_load_to_gNB, users_latency_to_gNB

def heuristic(n_CNs, n_GNBs, n_users, numerology, timestamp=0):
    # maximum latency value (delta max)
    delta_max = 1

    # migration cost constant
    migration_constant = 0.5 # range from 0.3 to 1.5

    # user latency considered in the first stage to the closest CN
    user_routing_latency = 0.02
    
    # read input files
    CNs, GNBs, Games, Users, Paths, Links, Links_latency, Links_bandwidth = read_input_files(n_CNs, n_GNBs, n_users, timestamp)

    solution = {"Total_Cost": 0, "time": 0, "Used_CNs": [], "users": {}, "migration_cost": 0}

    # get user's computational requirements based on image quality and throughput
    if n_users <= 300:
        sol = json.load(open("../solutions/first_stage/optimal_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_GNBs, n_users, timestamp), 'r'))
    else:
        sol = json.load(open("../solutions/first_stage/QoE_aware_heuristic/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_GNBs, n_users, timestamp), 'r'))

    users_CPU_demand, users_RAM_demand, users_GPU_demand, users_total_load, users_load_to_gNB, users_latency_to_gNB = get_users_game_requirements(Users, Games, sol)

    # if it is not the first timestamp, we load the last timestamp solution to get the users' last CNs and calculate the migration cost
    if timestamp > 1:
        last_timestamp_solution = json.load(open("../solutions/second_stage/heuristic/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_GNBs, n_users, timestamp-1), 'r'))

        users_last_CN = {}
        for user in Users:
            for u in last_timestamp_solution["solution"]["users"]:
                if u == str(user.my_ID()):
                    users_last_CN[user.ID] = last_timestamp_solution["solution"]["users"][u]["used_CN"]
                    break

    # users list of prefered feasible CNs by cost
    users_prefered_CNs = {}
    # latency of users to the current CN (closest CN)
    users_max_experienced_latency = {}
    # (User, CN) available paths)
    User_BS_CN_paths = {}
    start_time = time.time()
    # calculating users maximum experienced latency
    for user in Users:
        latency = 0
        for bs in users_latency_to_gNB[user.my_ID()].keys():
            if users_latency_to_gNB[user.my_ID()][bs] - user_routing_latency > latency:
                latency = users_latency_to_gNB[user.my_ID()][bs] - user_routing_latency
        users_max_experienced_latency[user.my_ID()] = latency

    # calculating users prefered CNs by cost
    for user in Users:
        CN_list = []
        cost_list = []
        for bs in users_load_to_gNB[user.my_ID()].keys():
            bs = int(bs)
            for p in Paths:
                # vefiry if the path is feasible in terms of latency to transmit user's video trasmission data without exceeding the maximum latency
                if p.my_destination() == bs and users_max_experienced_latency[user.ID] + (p.my_latency()/1000) <= delta_max:
                    if (user.my_ID(), bs, p.my_source()) not in User_BS_CN_paths:
                        User_BS_CN_paths[(user.my_ID(), bs, p.my_source())] = []
                    User_BS_CN_paths[(user.my_ID(), bs, p.my_source())].append(p)
                    if p.my_source() not in CN_list:
                        CN_list.append(p.my_source())
                        for cn in CNs:
                            if cn.my_ID() == p.my_source():
                                cost_list.append(cn.my_Fixed_cost())
                                break
        # sort the list of prefered CNs by cost
        sorted_CN_list = [cn for _, cn in sorted(zip(cost_list, CN_list))]
        users_prefered_CNs[user.my_ID()] = sorted_CN_list

    # list of activated CNs
    activated_CNs = []
    # placement of users applications
    users_application_placement = {}
    # paths available bandwidth
    paths_available_bandwidth = {}

    for p in Paths:
        paths_available_bandwidth[p.my_ID()] = min(Links_bandwidth[(link[0], link[1])] * 10 ** 6 for link in p.my_links())
    
    # placement fixed cost
    fixed_cost = 0
    # placement variable cost
    variable_cost = 0
    # placement migration cost
    migration_cost = 0

    for user in Users:
        for cn in users_prefered_CNs[user.my_ID()]:
            # if activated, we check if the CN has enough resources to host the user application
            for c in CNs:
                if c.my_ID() == cn:
                    if True:
                        # check if the paths between users BSs and the CN has enough bandwidth to transmit the user's video data
                        # this flag controls if the placement is feasible considering all BSs that the user is associated with
                        placement_is_feasible = True
                        for bs in users_load_to_gNB[user.my_ID()].keys():
                            bs = int(bs)
                            if (user.my_ID(), bs, c.my_ID()) in User_BS_CN_paths.keys():
                                for p in User_BS_CN_paths[(user.my_ID(), bs, c.my_ID())]:
                                    if paths_available_bandwidth[p.my_ID()] < users_load_to_gNB[user.my_ID()][str(bs)]/len(User_BS_CN_paths[(user.my_ID(), bs, c.my_ID())]):
                                            placement_is_feasible = False
                                            break
                                break
                        if placement_is_feasible:
                            # update links available bandwidth according to BSs load
                            for bs in users_load_to_gNB[user.my_ID()].keys():
                                bs = int(bs)
                                if (user.my_ID(), bs, c.my_ID()) in User_BS_CN_paths.keys():
                                    for p in User_BS_CN_paths[(user.my_ID(), bs, c.my_ID())]:
                                        for link in p.my_links():
                                            Links_bandwidth[(link[0], link[1])] -= (users_load_to_gNB[user.my_ID()][str(bs)]/len(User_BS_CN_paths[(user.my_ID(), bs, c.my_ID())]))/(10 ** 6)
                            lower_bw = 99999999999
                            for p in Paths:
                                paths_available_bandwidth[p.my_ID()] = min(Links_bandwidth[(link[0], link[1])] * 10 ** 6 for link in p.my_links())
                                for link in p.my_links():
                                    if Links_bandwidth[(link[0], link[1])] * 10 ** 6 < lower_bw:
                                        lower_bw = Links_bandwidth[(link[0], link[1])] * 10 ** 6
                                        lin = (link[0], link[1])
                            # print("USER {} - Link {} has lower BW {}".format(user.my_ID(), lin, lower_bw))
                            
                            users_application_placement[user.my_ID()] = cn
                            break
            if placement_is_feasible:
                # if the CN is activated, we add it to the list of activated CNs
                if c.my_ID() not in activated_CNs:
                    activated_CNs.append(c.my_ID())
                    fixed_cost += c.my_Fixed_cost()
                variable_cost += users_CPU_demand[user.my_ID()] * c.Variable_cost["CPU"] + users_GPU_demand[user.my_ID()] * c.Variable_cost["GPU"] + users_RAM_demand[user.my_ID()] * c.Variable_cost["RAM"] + (users_total_load[user.my_ID()]/(10**6))* c.Variable_cost["NET"]
                if timestamp > 1:
                    if users_last_CN[user.my_ID()] != c.my_ID():
                        migration_cost +=  migration_constant
                user_latency = 0
                for bs in users_load_to_gNB[user.my_ID()].keys():
                    bs = int(bs)
                    if (user.my_ID(), bs, c.my_ID()) in User_BS_CN_paths.keys():
                        for p in User_BS_CN_paths[(user.my_ID(), bs, c.my_ID())]:
                            if p.my_latency()/1000 + (users_latency_to_gNB[user.ID][str(bs)] - user_routing_latency) > user_latency:
                                user_latency = p.my_latency()/1000 + (users_latency_to_gNB[user.ID][str(bs)] - user_routing_latency)
                solution["users"][user.my_ID()] = {}
                solution["users"][user.my_ID()]["max_latency"] = user_latency
                solution["users"][user.my_ID()]["used_CN"] = c.my_ID()
                break
            else:
                # print("User {} cannot be placed in CN {} due to insufficient resources or bandwidth.".format(user.my_ID(), cn))
                pass
    end_time = time.time()
    
    solution["time"] = end_time - start_time
    
    solution["Used_CNs"] = activated_CNs

    for p in paths_available_bandwidth:
        if paths_available_bandwidth[p] < 0:
            print("Error: Path {} has negative available bandwidth: {}".format(p, paths_available_bandwidth[p]))
            sys.exit(1)

    print("Fixed cost: {}".format(fixed_cost))
    print("Variable cost: {}".format(variable_cost))
    print("Migration cost: {}".format(migration_cost))
    solution["migration_cost"] = migration_cost
    print("Total cost: {}".format(fixed_cost + variable_cost + migration_cost))
    solution["Total_Cost"] = fixed_cost + variable_cost + migration_cost
    for user in Users:
        if user.my_ID() not in users_application_placement:
            print("Error: User {} was not placed in any CN.".format(user.my_ID()))
    print("solved timestamp {}".format(timestamp))
    json.dump({"solution": solution}, open("../solutions/second_stage/heuristic/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_GNBs, n_users, timestamp), 'w'), indent=4)


if __name__ == "__main__":
    n_CNs = int(sys.argv[1])
    n_GNBs = int(sys.argv[2])
    n_users = int(sys.argv[3])
    numerology = 1
    for t in range(0, 100):
        heuristic(n_CNs, n_GNBs, n_users, numerology, timestamp=t)